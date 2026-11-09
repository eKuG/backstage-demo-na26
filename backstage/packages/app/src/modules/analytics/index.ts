import {
  configApiRef,
  createFrontendModule,
  identityApiRef,
} from '@backstage/frontend-plugin-api';
import { AnalyticsImplementationBlueprint } from '@backstage/plugin-app-react';
import { OtlpAnalytics } from './OtlpAnalytics';

export const analyticsModule = createFrontendModule({
  pluginId: 'app',
  extensions: [
    AnalyticsImplementationBlueprint.make({
      name: 'otlp',
      params: defineParams =>
        defineParams({
          deps: { configApi: configApiRef, identityApi: identityApiRef },
          factory: ({ configApi, identityApi }) =>
            new OtlpAnalytics({
              endpoint:
                configApi.getOptionalString('app.analytics.otlp.endpoint') ??
                'http://localhost:4318/v1/logs',
              identityApi,
            }),
        }),
    }),
  ],
});
