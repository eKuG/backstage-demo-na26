import { createApp } from '@backstage/frontend-defaults';
import catalogPlugin from '@backstage/plugin-catalog/alpha';
import { navModule } from './modules/nav';
import { homeModule } from './modules/home';
import { analyticsModule } from './modules/analytics';

export default createApp({
  features: [catalogPlugin, navModule, homeModule, analyticsModule],
});
