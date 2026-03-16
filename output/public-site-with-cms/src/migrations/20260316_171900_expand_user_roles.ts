import { sql } from "@payloadcms/db-postgres";
import type { MigrateDownArgs, MigrateUpArgs } from "@payloadcms/db-postgres";

export async function up({ db }: MigrateUpArgs): Promise<void> {
  await db.execute(sql`
   ALTER TYPE "public"."enum_users_role" RENAME TO "enum_users_role_old";
  CREATE TYPE "public"."enum_users_role" AS ENUM('admin', 'editor', 'reviewer', 'user');
  ALTER TABLE "users" ALTER COLUMN "role" DROP DEFAULT;
  ALTER TABLE "users" ALTER COLUMN "role" TYPE "public"."enum_users_role" USING ("role"::text::"public"."enum_users_role");
  ALTER TABLE "users" ALTER COLUMN "role" SET DEFAULT 'user';
  DROP TYPE "public"."enum_users_role_old";`);
}

export async function down({ db }: MigrateDownArgs): Promise<void> {
  await db.execute(sql`
   ALTER TYPE "public"."enum_users_role" RENAME TO "enum_users_role_old";
  CREATE TYPE "public"."enum_users_role" AS ENUM('admin', 'user');
  ALTER TABLE "users" ALTER COLUMN "role" DROP DEFAULT;
  ALTER TABLE "users" ALTER COLUMN "role" TYPE "public"."enum_users_role" USING ((CASE WHEN "role"::text = 'admin' THEN 'admin' ELSE 'user' END)::"public"."enum_users_role");
  ALTER TABLE "users" ALTER COLUMN "role" SET DEFAULT 'user';
  DROP TYPE "public"."enum_users_role_old";`);
}
