import * as migration_20260316_144712_st008_bootstrap from "./20260316_144712_st008_bootstrap.ts";
import * as migration_20260316_151531_st009_backend_bootstrap from "./20260316_151531_st009_backend_bootstrap.ts";
import * as migration_20260316_153530_st001_define_cms_content_model from "./20260316_153530_st001_define_cms_content_model.ts";
import * as migration_20260316_160542 from "./20260316_160542.ts";
import * as migration_20260316_165741_add_user_roles from "./20260316_165741_add_user_roles.ts";
import * as migration_20260316_171900_expand_user_roles from "./20260316_171900_expand_user_roles.ts";
import * as migration_20260316_175433_st016_scheduled_publishing from "./20260316_175433_st016_scheduled_publishing.ts";

export const migrations = [
  {
    up: migration_20260316_144712_st008_bootstrap.up,
    down: migration_20260316_144712_st008_bootstrap.down,
    name: "20260316_144712_st008_bootstrap",
  },
  {
    up: migration_20260316_151531_st009_backend_bootstrap.up,
    down: migration_20260316_151531_st009_backend_bootstrap.down,
    name: "20260316_151531_st009_backend_bootstrap",
  },
  {
    up: migration_20260316_153530_st001_define_cms_content_model.up,
    down: migration_20260316_153530_st001_define_cms_content_model.down,
    name: "20260316_153530_st001_define_cms_content_model",
  },
  {
    up: migration_20260316_160542.up,
    down: migration_20260316_160542.down,
    name: "20260316_160542",
  },
  {
    up: migration_20260316_165741_add_user_roles.up,
    down: migration_20260316_165741_add_user_roles.down,
    name: "20260316_165741_add_user_roles",
  },
  {
    up: migration_20260316_171900_expand_user_roles.up,
    down: migration_20260316_171900_expand_user_roles.down,
    name: "20260316_171900_expand_user_roles",
  },
  {
    up: migration_20260316_175433_st016_scheduled_publishing.up,
    down: migration_20260316_175433_st016_scheduled_publishing.down,
    name: "20260316_175433_st016_scheduled_publishing",
  },
];
