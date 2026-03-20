import * as migration_20260320_124220 from './20260320_124220';
import * as migration_20260320_130145 from './20260320_130145';
import * as migration_20260320_135004_cms_content_model_part_1 from './20260320_135004_cms_content_model_part_1';

export const migrations = [
  {
    up: migration_20260320_124220.up,
    down: migration_20260320_124220.down,
    name: '20260320_124220',
  },
  {
    up: migration_20260320_130145.up,
    down: migration_20260320_130145.down,
    name: '20260320_130145',
  },
  {
    up: migration_20260320_135004_cms_content_model_part_1.up,
    down: migration_20260320_135004_cms_content_model_part_1.down,
    name: '20260320_135004_cms_content_model_part_1'
  },
];
