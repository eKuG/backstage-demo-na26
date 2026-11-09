import type {
  AnalyticsEvent,
  AnalyticsImplementation,
  IdentityApi,
} from '@backstage/frontend-plugin-api';

/**
 * Backstage AnalyticsApi -> OpenTelemetry log records, posted as OTLP/JSON to a Collector.
 * No SDK in the browser: ~60 lines, one fetch every two seconds.
 * Each event becomes a log record; the Collector's count connector turns them into metrics.
 */
type AnyValue =
  | { stringValue: string }
  | { intValue: string }
  | { doubleValue: number }
  | { boolValue: boolean };

const toAnyValue = (v: unknown): AnyValue => {
  if (typeof v === 'number') {
    return Number.isInteger(v) ? { intValue: String(v) } : { doubleValue: v };
  }
  if (typeof v === 'boolean') return { boolValue: v };
  return { stringValue: String(v) };
};

export class OtlpAnalytics implements AnalyticsImplementation {
  private queue: object[] = [];
  private userRef = 'anonymous';
  private readonly sessionId: string;

  constructor(
    private readonly opts: { endpoint: string; identityApi: IdentityApi },
  ) {
    const key = 'otel.session.id';
    this.sessionId =
      window.sessionStorage.getItem(key) ?? window.crypto.randomUUID();
    window.sessionStorage.setItem(key, this.sessionId);
    opts.identityApi
      .getBackstageIdentity()
      .then(id => {
        this.userRef = id.userEntityRef;
      })
      .catch(() => undefined);
    window.setInterval(() => this.flush(), 2000);
    window.addEventListener('pagehide', () => this.flush());
  }

  captureEvent(event: AnalyticsEvent): void {
    const attrs: Record<string, unknown> = {
      'backstage.analytics.action': event.action,
      'backstage.analytics.subject': event.subject,
      'backstage.plugin': event.context.pluginId ?? 'unknown',
      'enduser.id': this.userRef,
      'session.id': this.sessionId,
      'url.path': window.location.pathname,
    };
    if (event.value !== undefined) {
      attrs['backstage.analytics.value'] = event.value;
    }
    if (event.action === 'search') {
      attrs['backstage.search.zero_results'] = String(event.value === 0);
    }
    for (const [k, v] of Object.entries(event.context)) {
      if (v !== undefined && k !== 'pluginId') attrs[`backstage.context.${k}`] = v;
    }
    for (const [k, v] of Object.entries(event.attributes ?? {})) {
      attrs[`backstage.attr.${k}`] = v;
    }
    this.queue.push({
      timeUnixNano: `${Date.now()}000000`,
      severityNumber: 9,
      severityText: 'INFO',
      body: { stringValue: `${event.action} ${event.subject}` },
      attributes: Object.entries(attrs).map(([key, value]) => ({
        key,
        value: toAnyValue(value),
      })),
    });
  }

  private flush(): void {
    if (this.queue.length === 0) return;
    const logRecords = this.queue;
    this.queue = [];
    const body = JSON.stringify({
      resourceLogs: [
        {
          resource: {
            attributes: [
              { key: 'service.name', value: { stringValue: 'backstage-frontend' } },
              { key: 'service.namespace', value: { stringValue: 'idp' } },
              { key: 'deployment.environment.name', value: { stringValue: 'demo' } },
              { key: 'browser.language', value: { stringValue: navigator.language } },
            ],
          },
          scopeLogs: [{ scope: { name: 'backstage.analytics' }, logRecords }],
        },
      ],
    });
    fetch(this.opts.endpoint, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body,
      keepalive: true,
    }).catch(() => undefined);
  }
}
