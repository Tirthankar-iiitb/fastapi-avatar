from fastapi import APIRouter, File, UploadFile, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import tempfile
import os
import whisper
from gtts import gTTS
from typing import Dict, Any
from pydantic import BaseModel
import uuid
from ..utils.helpers import replyback  # Import your helper function

# Create router for whisper endpoints
router = APIRouter(
    prefix="/api",
    tags=["transcription"]
)

# @router.post("/whisper-transcription")
@router.post("/transcribe")
async def whisper_transcription(audio: UploadFile = File(...)) -> Dict[str, Any]:
    """
    API endpoint for transcribing speech using Whisper
    """
    
    if not audio.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Audio file is required"
        )
    
    tmp_file_path = None
    
    try:
        # Create temporary file
        suffix = '.webm'
        if audio.filename:
            _, ext = os.path.splitext(audio.filename)
            if ext:
                suffix = ext
        
        # Save uploaded file
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            content = await audio.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        # Process with Whisper
        model = whisper.load_model("base")
        result = model.transcribe(tmp_file_path)
        transcription = result["text"]
        query_response = replyback(transcription)
        
        return {
            "status": "success",
            "transcription": transcription,
            "query_response": query_response
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing audio: {str(e)}"
        )
        
    finally:
        if tmp_file_path and os.path.exists(tmp_file_path):
            try:
                os.unlink(tmp_file_path)
            except OSError:
                pass


# Response models
class TTSResponse(BaseModel):
    message: str
    audio_url: str

class ErrorResponse(BaseModel):
    error: str


# @router.post("/whisper-tts", response_model=TTSResponse)
@router.post("/transcribetts", response_model=TTSResponse)
async def whisper_transcription_tts(
    audio: UploadFile = File(..., description="Audio file to transcribe")
) -> Dict[str, Any]:
    """
    API endpoint for transcribing speech using Whisper and converting 
    LLM generated response to speech using TTS
    
    Args:
        audio: Audio file to transcribe (multipart/form-data)
        
    Returns:
        Dict containing success message and audio URL
        
    Raises:
        HTTPException: If no audio file provided or processing error occurs
    """
    
    # Validate file upload
    if not audio.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Audio file is required"
        )
    
    tmp_file_path = None
    
    try:
        # Create temporary file with proper suffix
        suffix = '.webm'
        if audio.filename:
            _, ext = os.path.splitext(audio.filename)
            if ext:
                suffix = ext
        
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            content = await audio.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        # Load Whisper model
        model = whisper.load_model("base")
        
        # Transcribe audio
        result = model.transcribe(tmp_file_path)
        transcription = result["text"]
        
        # Process transcription with your custom function
        # transcription = modify_text(transcription)  # Uncomment if you have this
        query_response = replyback(transcription)  # Make sure this function exists
        
        # Clean up the temporary transcription file
        os.unlink(tmp_file_path)
        tmp_file_path = None  # Reset to avoid double cleanup
        
        # Check if we got a valid response
        if not query_response or query_response.strip() == "":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="No valid response generated from transcription"
            )
        
        # Generate TTS audio
        tts = gTTS(text=query_response, lang='en')
        
        # Create media directory if it doesn't exist
        os.makedirs('media', exist_ok=True)
        
        # Generate unique filename to avoid conflicts
        unique_id = str(uuid.uuid4())[:8]
        audio_filename = f'speech_{unique_id}.mp3'
        audio_path = f'media/{audio_filename}'
        
        # Save TTS audio
        tts.save(audio_path)
        
        return {
            "message": "Text converted to speech",
            "audio_url": f"/{audio_path}"
        }
        
    except Exception as e:
        # Clean up temporary file in case of error
        if tmp_file_path and os.path.exists(tmp_file_path):
            try:
                os.unlink(tmp_file_path)
            except OSError:
                pass
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing audio: {str(e)}"
        )


# Alternative version with more detailed response including transcription
class DetailedTTSResponse(BaseModel):
    message: str
    audio_url: str
    transcription: str
    query_response: str

@router.post("/whisper-tts-detailed", response_model=DetailedTTSResponse)
async def whisper_transcription_tts_detailed(
    audio: UploadFile = File(..., description="Audio file to transcribe")
) -> DetailedTTSResponse:
    """
    Enhanced version that returns both transcription and TTS audio
    """
    
    if not audio.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Audio file is required"
        )
    
    tmp_file_path = None
    
    try:
        # File processing (same as above)
        suffix = '.webm'
        if audio.filename:
            _, ext = os.path.splitext(audio.filename)
            if ext:
                suffix = ext
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            content = await audio.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        # Whisper transcription
        model = whisper.load_model("base")
        result = model.transcribe(tmp_file_path)
        transcription = result["text"]
        query_response = replyback(transcription)
        
        # Cleanup
        os.unlink(tmp_file_path)
        tmp_file_path = None
        
        if not query_response or query_response.strip() == "":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="No valid response generated from transcription"
            )
        
        # TTS Generation
        tts = gTTS(text=query_response, lang='en')
        os.makedirs('media', exist_ok=True)
        
        unique_id = str(uuid.uuid4())[:8]
        audio_filename = f'speech_{unique_id}.mp3'
        audio_path = f'media/{audio_filename}'
        tts.save(audio_path)
        
        return DetailedTTSResponse(
            message="Text converted to speech",
            audio_url=f"/{audio_path}",
            transcription=transcription,
            query_response=query_response
        )
        
    except Exception as e:
        if tmp_file_path and os.path.exists(tmp_file_path):
            try:
                os.unlink(tmp_file_path)
            except OSError:
                pass
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing audio: {str(e)}"
        )
    

