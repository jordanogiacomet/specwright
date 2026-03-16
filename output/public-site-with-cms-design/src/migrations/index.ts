import * as migration_20260316_000000_bootstrap_database from './20260316_000000_bootstrap_database';
import * as migration_20260316_183255_setup_backend_service from './20260316_183255_setup_backend_service';
import * as migration_20260316_185446_st_001_define_cms_content_model from './20260316_185446_st_001_define_cms_content_model';
import * as migration_20260316_192016_st_003_add_locale_support from './20260316_192016_st_003_add_locale_support';
import * as migration_20260316_200000_st_012_implement_role_based_access_control from './20260316_200000_st_012_implement_role_based_access_control';

export const migrations = [
  {
    up: migration_20260316_000000_bootstrap_database.up,
    down: migration_20260316_000000_bootstrap_database.down,
    name: '20260316_000000_bootstrap_database',
  },
  {
    up: migration_20260316_183255_setup_backend_service.up,
    down: migration_20260316_183255_setup_backend_service.down,
    name: '20260316_183255_setup_backend_service',
  },
  {
    up: migration_20260316_185446_st_001_define_cms_content_model.up,
    down: migration_20260316_185446_st_001_define_cms_content_model.down,
    name: '20260316_185446_st_001_define_cms_content_model',
  },
  {
    up: migration_20260316_192016_st_003_add_locale_support.up,
    down: migration_20260316_192016_st_003_add_locale_support.down,
    name: '20260316_192016_st_003_add_locale_support'
  },
  {
    up: migration_20260316_200000_st_012_implement_role_based_access_control.up,
    down: migration_20260316_200000_st_012_implement_role_based_access_control.down,
    name: '20260316_200000_st_012_implement_role_based_access_control'
  },
];
