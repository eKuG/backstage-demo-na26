export interface Config {
  app?: {
    analytics?: {
      otlp?: {
        /**
         * OTLP/HTTP logs endpoint that receives frontend AnalyticsApi events.
         * @visibility frontend
         */
        endpoint?: string;
      };
    };
  };
}
