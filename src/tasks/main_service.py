from mini_rag.celery_app import celery_app
import logging
from datetime import datetime
import asyncio

logger = logging.getLogger("celery.task")

@celery_app.task(bind=True, name="send_email_reports", acks_late=True)
def send_email_reports(self, main_wait_time: int):

  return asyncio.run(_send_email_reports(self, main_wait_time))

async def _send_email_reports(task_instance, main_wait_time: int):

  started_at = str(datetime.now())

  task_instance.update_state(
    state='PROGRESS', 
    meta={
      "started_at": started_at,
    }
  )

  # Simulate sending email reports
  for i in range(15):
    logger.info(f"Sending report {i + 1}...")
    await asyncio.sleep(main_wait_time)  # Simulate time taken to send a report
          
  return {
    "message": "All reports have been sent successfully.",
    "started_at": started_at,
    "completed_at": str(datetime.now())
  }
