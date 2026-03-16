import { getSessionUser } from "@/lib/auth";
import { adminRole, requireRole } from "@/lib/permissions";

export async function GET(request: Request) {
  const user = await getSessionUser(request.headers);
  const authorization = requireRole(user, adminRole);

  if (!authorization.ok) {
    return Response.json(
      {
        error: authorization.message,
      },
      { status: authorization.status },
    );
  }

  return Response.json(
    {
      authenticated: true,
      requiredRole: adminRole,
      user,
    },
    { status: 200 },
  );
}
