"""StreamsMixin — stream fork, significant events deploy and cleanup methods."""

from __future__ import annotations

import logging
import time

import httpx

from elastic_config.deployer_base import _es_headers, _kibana_headers, _retry_http, ProgressCallback

logger = logging.getLogger("deployer")

# Fork can fail on a cold cluster if logs.otel is not ready yet (integrations
# just installed) or Streams is still enabling. Match OTLP derivation pacing.
_STREAM_FORK_ROUNDS = 4
_STREAM_FORK_ROUND_DELAY = 5.0


class StreamsMixin:

    @property
    def _stream_name(self) -> str:
        return f"logs.otel.{self.ns}"

    @property
    def _ecs_stream_name(self) -> str:
        return f"logs.ecs.{self.ns}"

    @property
    def _ecs_wired_stream(self) -> str:
        """Wired-stream ingest endpoint. All scenarios POST to `logs.ecs/_bulk`;
        the deployer then forks `logs.ecs` into per-scenario partitions."""
        return "logs.ecs"

    def _stream_exists(self, client: httpx.Client, stream_name: str | None = None) -> bool:
        """Return True if the given stream (default: scenario OTLP child) is present."""
        name = stream_name or self._stream_name
        resp = client.get(
            f"{self.kibana_url}/api/streams/{name}",
            headers=_kibana_headers(self.api_key),
        )
        return resp.status_code == 200

    def _fork_stream(
        self,
        client: httpx.Client,
        *,
        parent: str,
        child: str,
        filter_field: str,
    ) -> bool:
        """Fork a parent stream into a child partition. Retries with backoff."""
        if self._stream_exists(client, child):
            return True

        fork_body = {
            "where": {"field": filter_field, "eq": self.ns},
            "status": "enabled",
            "stream": {"name": child},
        }
        fork_url = f"{self.kibana_url}/api/streams/{parent}/_fork"
        label = f"fork {child} from {parent}"

        for round_idx in range(_STREAM_FORK_ROUNDS):
            if round_idx > 0:
                time.sleep(_STREAM_FORK_ROUND_DELAY)

            resp = _retry_http(
                lambda: client.post(
                    fork_url,
                    headers=_kibana_headers(self.api_key),
                    json=fork_body,
                ),
                label=label,
            )
            if resp is not None and resp.status_code < 300 and self._stream_exists(client, child):
                return True
            if resp is not None and resp.status_code >= 300:
                logger.warning(
                    "%s failed (HTTP %s, round %d/%d): %s",
                    label,
                    resp.status_code,
                    round_idx + 1,
                    _STREAM_FORK_ROUNDS,
                    resp.text[:500],
                )

        return self._stream_exists(client, child)

    def _create_stream(self, client: httpx.Client) -> bool:
        """Fork logs.otel into a scenario-specific child stream."""
        return self._fork_stream(
            client,
            parent="logs.otel",
            child=self._stream_name,
            filter_field="resource.attributes.service.namespace",
        )

    def _create_ecs_stream(self, client: httpx.Client) -> bool:
        """Fork logs.ecs into this scenario's partition."""
        return self._fork_stream(
            client,
            parent=self._ecs_wired_stream,
            child=self._ecs_stream_name,
            filter_field="service.namespace",
        )

    def _delete_ecs_stream(self, client: httpx.Client) -> bool:
        """Delete only this scenario's partition. The base wired stream
        `logs.ecs` is managed by Elastic and shared across all scenarios.

        Returns True if the partition is gone (or never existed); False if it
        is still present after retries.
        """
        # 1. Delete the partition Streams entity (mirrors logs.otel teardown).
        resp = _retry_http(
            lambda: client.delete(
                f"{self.kibana_url}/api/streams/{self._ecs_stream_name}",
                headers=_kibana_headers(self.api_key),
            ),
            label=f"delete ECS partition {self._ecs_stream_name}",
        )
        deleted_ok = resp is not None and resp.status_code in (200, 204, 404)
        if not deleted_ok and resp is not None:
            logger.warning(
                "Delete ECS partition stream %s returned HTTP %s after retries",
                self._ecs_stream_name, resp.status_code,
            )

        # 2. Delete this scenario's docs from the wired stream so co-deployed
        #    scenarios aren't affected.
        try:
            client.post(
                f"{self.elastic_url}/{self._ecs_wired_stream}/_delete_by_query",
                headers=_es_headers(self.api_key),
                params={"refresh": "false", "wait_for_completion": "false"},
                json={"query": {"term": {"service.namespace": self.ns}}},
            )
        except Exception as exc:
            logger.info("ECS docs delete-by-query skipped: %s", exc)

        return deleted_ok

    def _deploy_significant_events(self, client: httpx.Client, notify: ProgressCallback):
        step = self._step(11)
        step.status = "running"
        notify(self.progress)

        # Delete any existing stream then recreate it clean
        self._delete_stream(client)
        if not self._create_stream(client):
            step.detail = (
                f"Failed to fork {self._stream_name} from logs.otel after "
                f"{_STREAM_FORK_ROUNDS} attempts (namespace={self.ns}). "
                "Check Streams is enabled and OTLP data is flowing into logs.otel."
            )
            step.status = "failed"
            notify(self.progress)
            return

        # Build bulk operations
        operations = []
        registry = self.scenario.channel_registry
        for ch_num, ch_data in sorted(registry.items()):
            num_str = f"{int(ch_num):02d}"
            error_type = ch_data["error_type"]
            esql_query = (
                f"FROM {self._stream_name},{self._stream_name}.* METADATA _id, _source"
                f' | WHERE body.text LIKE "*{error_type}*" AND severity_text == "ERROR"'
            )
            operations.append({
                "index": {
                    "id": f"{self.ns}-se-ch{num_str}",
                    "title": f"{self.scenario.scenario_name}: SE CH {num_str}: {ch_data['name']}",
                    "description": f"{ch_data.get('subsystem', 'system')} — {error_type}",
                    "esql": {"query": esql_query},
                }
            })

        step.items_total = len(operations)

        if operations:
            resp = client.post(
                f"{self.kibana_url}/api/streams/{self._stream_name}/queries/_bulk",
                headers=_kibana_headers(self.api_key),
                json={"operations": operations},
            )
            if resp.status_code < 300:
                step.items_done = len(operations)
                step.detail = f"Created {len(operations)} stream queries on {self._stream_name}"
            else:
                logger.warning("Significant events bulk create failed: %s", resp.text[:500])
                step.detail = f"Bulk create failed (HTTP {resp.status_code})"

        step.status = "ok" if step.items_done > 0 else "failed"
        notify(self.progress)

    def _delete_stream(self, client: httpx.Client) -> bool:
        """Delete the scenario-specific stream (also removes its significant events).

        Returns True if the stream is gone (deleted or 404), False if still present.
        """
        resp = _retry_http(
            lambda: client.delete(
                f"{self.kibana_url}/api/streams/{self._stream_name}",
                headers=_kibana_headers(self.api_key),
            ),
            label=f"delete stream {self._stream_name}",
        )
        if resp is None:
            return False
        if resp.status_code == 404 or resp.status_code < 300:
            return True
        logger.warning(
            "Failed to delete stream %s after retries: HTTP %s",
            self._stream_name, resp.status_code,
        )
        return False
