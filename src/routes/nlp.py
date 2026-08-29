from fastapi import APIRouter, Depends, status, Request
from fastapi.responses import JSONResponse
from models.ProjectModel import ProjectModel
from models.ChunkModel import ChunkModel
from .schemas.nlp import PushRequest, SearchRequest
from tasks.data_indexing import index_data_content
from controllers import NLPController
from models import ResponseSignals
from tqdm.auto import tqdm
import logging

logger = logging.getLogger('uvicorn.error')

nlp_router = APIRouter(
  prefix="/api/v1/nlp",
  tags=["api_v1", "nlp"],
)

@nlp_router.post("/index/push/{project_id}")
async def index_project_data(request: Request, project_id: int, push_request: PushRequest):

  task = index_data_content.delay(project_id=project_id, do_reset=push_request.do_reset)

  return JSONResponse(
    status_code=status.HTTP_202_ACCEPTED,
    content={
      "message": ResponseSignals.INDEXING_TASK_STARTED.value,
      "task_id": task.id
    }
  )

@nlp_router.get("/index/info/{project_id}")
async def get_project_index_info(request: Request, project_id: int):
  project_model = await ProjectModel.create_instance(db_client = request.app.state.db_client)
  
  project = await project_model.get_project_or_create_one(project_id)

  if not project:
    return JSONResponse(
      status_code=status.HTTP_404_NOT_FOUND,
      content={"message": ResponseSignals.PROJECT_NOT_FOUND.value}
    )

  nlp_controller = NLPController(
      vectordb_client = request.app.state.vector_db_client,
      embedding_client = request.app.state.embedding_client, 
      generation_client = request.app.state.generation_client,
      template_parser = request.app.state.template_parser
    )

  collection_index_info = await nlp_controller.get_vector_db_collection_info(project)

  return JSONResponse(
    status_code=status.HTTP_200_OK,
    content={
      "message": ResponseSignals.GET_INDEX_INFO_SUCCESS.value,
      "index_info": collection_index_info
    }
  )

@nlp_router.post("/index/search/{project_id}")
async def search_project_data(request: Request, project_id: int, search_request: SearchRequest):
  
  project_model = await ProjectModel.create_instance(db_client = request.app.state.db_client)
  
  project = await project_model.get_project_or_create_one(project_id)

  if not project:
    return JSONResponse(
      status_code=status.HTTP_404_NOT_FOUND,
      content={"message": ResponseSignals.PROJECT_NOT_FOUND.value}
    )

  nlp_controller = NLPController(
    vectordb_client = request.app.state.vector_db_client,
    embedding_client = request.app.state.embedding_client, 
    generation_client = request.app.state.generation_client,
    template_parser = request.app.state.template_parser
  )

  search_results = await nlp_controller.search_in_vector_db(project, search_request.text, search_request.top_k)

  if not search_results:
    return JSONResponse(
      status_code=status.HTTP_404_NOT_FOUND,
      content={"message": ResponseSignals.VECTOR_SEARCH_SUCCESS_NO_RESULTS.value}
    )

  return JSONResponse(
    status_code=status.HTTP_200_OK,
    content={
      "message": ResponseSignals.VECTOR_SEARCH_SUCCESS.value,
      "results": [result.model_dump() for result in search_results]
    }
  )


@nlp_router.post("/index/answer/{project_id}")
async def answer_rag_query(request: Request, project_id: int, search_request: SearchRequest):
  
  project_model = await ProjectModel.create_instance(db_client = request.app.state.db_client)
  
  project = await project_model.get_project_or_create_one(project_id)

  if not project:
    return JSONResponse(
      status_code=status.HTTP_404_NOT_FOUND,
      content={"message": ResponseSignals.PROJECT_NOT_FOUND.value}
    )

  nlp_controller = NLPController(
    vectordb_client = request.app.state.vector_db_client,
    embedding_client = request.app.state.embedding_client, 
    generation_client = request.app.state.generation_client,
    template_parser = request.app.state.template_parser
  )

  answer, full_prompt, chat_history = await nlp_controller.answer_rag_query(
    project, 
    search_request.text, 
    search_request.top_k
  )

  if not answer:
    return JSONResponse(
      status_code=status.HTTP_400_BAD_REQUEST,
      content={"message": ResponseSignals.RAG_QUERY_ANSWER_FAILED.value}
    )

  return JSONResponse(
    status_code=status.HTTP_200_OK,
    content={
      "message": ResponseSignals.RAG_QUERY_ANSWER_SUCCESS.value,
      "answer": answer,
      "full_prompt": full_prompt,
      "chat_history": chat_history
    }
  )
