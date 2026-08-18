from enum import Enum

class ResponseSignals(Enum):
  FILE_VALIDATION_SUCCESS = "File validation successful."
  FILE_TYPE_NOT_ALLOWED = "File type not allowed."
  FILE_SIZE_EXCEEDS_LIMIT = "File size exceeds the maximum limit."
  FILE_UPLOADED_SUCCESSFULLY = "File uploaded successfully."
  FILE_UPLOADED_FAILED = "File upload failed."
  FILE_PROCESSED_SUCCESSFULLY = "File processing successful."
  FILE_PROCESSED_FAILED = "File processing failed."
  NO_FILES_FOUND_FOR_PROCESSING = "No files found for processing."
  FILE_NOT_FOUND = "File not found."
