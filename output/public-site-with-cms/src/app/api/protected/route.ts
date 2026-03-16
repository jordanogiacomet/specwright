import { getCurrentUserFromRequest } from "@/lib/auth";
import { withObservedRoute } from "@/lib/observability";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

const handleGet = async (request: Request) => {
  const currentUser = await getCurrentUserFromRequest(request);

  if (!currentUser) {
    return Response.json(
      {
        message: "Unauthorized",
      },
      {
        headers: {
          "Cache-Control": "no-store",
        },
        status: 401,
      },
    );
  }

  return Response.json(
    {
      authenticated: true,
      user: currentUser,
    },
    {
      headers: {
        "Cache-Control": "no-store",
      },
      status: 200,
    },
  );
};

export const GET = withObservedRoute({
  handler: handleGet,
  route: "/api/protected",
  service: "api",
});
