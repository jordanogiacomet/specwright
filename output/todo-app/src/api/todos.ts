import {
  Router,
  type ErrorRequestHandler,
  type Request,
  type RequestHandler,
  type Response,
} from "express";

import { requireAuth } from "../lib/auth";
import { createLogger } from "../lib/logger";
import {
  type ListTodosOptions,
  createTodo,
  deleteTodo,
  listTodosForUser,
  todoAssignmentFilters,
  TodoNotFoundError,
  todoSortFields,
  todoSortOrders,
  type TodoAssignmentFilter,
  TodoValidationError,
  type TodoSortField,
  type TodoSortOrder,
  updateTodo,
} from "../models/todo";

const todosLogger = createLogger({
  component: "todos-router",
  service: "todo-app-api",
});

function getSingleQueryValue(
  value: unknown,
  fieldName: string,
): string | undefined {
  if (value === undefined) {
    return undefined;
  }

  if (Array.isArray(value)) {
    throw new TodoValidationError(`${fieldName} must be provided only once.`);
  }

  if (typeof value !== "string") {
    throw new TodoValidationError(`${fieldName} must be a string.`);
  }

  return value;
}

function parseListTodosQuery(request: Request): ListTodosOptions {
  const assignmentValue = getSingleQueryValue(
    request.query.assignment,
    "assignment",
  );
  const completedValue = getSingleQueryValue(
    request.query.completed,
    "completed",
  );
  const overdueValue = getSingleQueryValue(request.query.overdue, "overdue");
  const sortValue = getSingleQueryValue(request.query.sort, "sort");
  const orderValue = getSingleQueryValue(request.query.order, "order");

  let assignment: TodoAssignmentFilter | undefined;
  let completed: boolean | undefined;
  let overdue: boolean | undefined;

  if (assignmentValue !== undefined) {
    if (
      !todoAssignmentFilters.includes(assignmentValue as TodoAssignmentFilter)
    ) {
      throw new TodoValidationError(
        `assignment must be one of: ${todoAssignmentFilters.join(", ")}.`,
      );
    }

    assignment = assignmentValue as TodoAssignmentFilter;
  }

  if (completedValue === "true") {
    completed = true;
  } else if (completedValue === "false") {
    completed = false;
  } else if (completedValue !== undefined) {
    throw new TodoValidationError("completed must be 'true' or 'false'.");
  }

  if (overdueValue === "true") {
    overdue = true;
  } else if (overdueValue === "false") {
    overdue = false;
  } else if (overdueValue !== undefined) {
    throw new TodoValidationError("overdue must be 'true' or 'false'.");
  }

  let sort: TodoSortField | undefined;

  if (sortValue !== undefined) {
    if (!todoSortFields.includes(sortValue as TodoSortField)) {
      throw new TodoValidationError(
        `sort must be one of: ${todoSortFields.join(", ")}.`,
      );
    }

    sort = sortValue as TodoSortField;
  }

  let order: TodoSortOrder | undefined;

  if (orderValue !== undefined) {
    if (!todoSortOrders.includes(orderValue as TodoSortOrder)) {
      throw new TodoValidationError(
        `order must be one of: ${todoSortOrders.join(", ")}.`,
      );
    }

    order = orderValue as TodoSortOrder;
  }

  return {
    assignment,
    completed,
    overdue,
    sort,
    order,
  };
}

function asyncHandler(
  handler: (request: Request, response: Response) => Promise<void>,
): RequestHandler {
  return (request, response, next) => {
    void handler(request, response).catch(next);
  };
}

const listTodosHandler = asyncHandler(async (request, response) => {
  const todos = await listTodosForUser(
    request.auth!.user.id,
    parseListTodosQuery(request),
  );

  response.status(200).json({
    items: todos,
  });
});

const createTodoHandler = asyncHandler(async (request, response) => {
  const todo = await createTodo(request.auth!.user.id, request.body);

  response.status(201).json(todo);
});

const updateTodoHandler = asyncHandler(async (request, response) => {
  const todo = await updateTodo(
    request.params.id,
    request.auth!.user.id,
    request.body,
  );

  response.status(200).json(todo);
});

const deleteTodoHandler = asyncHandler(async (request, response) => {
  await deleteTodo(request.params.id, request.auth!.user.id);

  response.status(204).send();
});

const todosErrorHandler: ErrorRequestHandler = (error, _request, response) => {
  if (error instanceof TodoValidationError) {
    response.status(400).json({
      error: error.name,
      message: error.message,
    });
    return;
  }

  if (error instanceof TodoNotFoundError) {
    response.status(404).json({
      error: error.name,
      message: error.message,
    });
    return;
  }

  todosLogger.error("Unexpected todos API error", {
    error,
  });
  response.status(500).json({
    error: "InternalServerError",
    message: "Unexpected error while handling todo request.",
  });
};

const todosRouter = Router();

todosRouter.use(requireAuth);

todosRouter.get("/", listTodosHandler);
todosRouter.post("/", createTodoHandler);
todosRouter.patch("/:id", updateTodoHandler);
todosRouter.delete("/:id", deleteTodoHandler);

todosRouter.use(todosErrorHandler);

export { todosRouter };
