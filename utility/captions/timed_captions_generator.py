import whisper
import re

def generate_timed_captions(audio_filename, model_size="base"):
    WHISPER_MODEL = whisper.load_model(model_size)
    
    # Forçar português e desabilitar detecção automática
    result = WHISPER_MODEL.transcribe(
        audio_filename, 
        language="pt", 
        task="transcribe",
        verbose=False,
        fp16=False
    )
    
    return getCaptionsWithTime(result)

def splitWordsBySize(words, maxCaptionSize):
   
    halfCaptionSize = maxCaptionSize / 2
    captions = []
    while words:
        caption = words[0]
        words = words[1:]
        while words and len(caption + ' ' + words[0]) <= maxCaptionSize:
            caption += ' ' + words[0]
            words = words[1:]
            if len(caption) >= halfCaptionSize and words:
                break
        captions.append(caption)
    return captions

def getTimestampMapping(whisper_analysis):
   
    index = 0
    locationToTimestamp = {}
    for segment in whisper_analysis['segments']:
        # Para Whisper padrão, usamos o segmento completo
        text = segment['text']
        start_time = segment['start']
        end_time = segment['end']
        
        # Dividir o texto em palavras
        words = text.split()
        word_duration = (end_time - start_time) / len(words) if words else 0
        
        for i, word in enumerate(words):
            word_start = start_time + (i * word_duration)
            word_end = start_time + ((i + 1) * word_duration)
            
            newIndex = index + len(word) + 1
            locationToTimestamp[(index, newIndex)] = word_end
            index = newIndex
    
    return locationToTimestamp

def cleanWord(word):
   
    return re.sub(r'[^\w\s\-_"\'\']', '', word)

def interpolateTimeFromDict(word_position, d):
   
    for key, value in d.items():
        if key[0] <= word_position <= key[1]:
            return value
    return None

def getCaptionsWithTime(whisper_analysis, maxCaptionSize=15, considerPunctuation=False):
   
    wordLocationToTime = getTimestampMapping(whisper_analysis)
    position = 0
    start_time = 0
    CaptionsPairs = []
    text = whisper_analysis['text']
    
    if considerPunctuation:
        sentences = re.split(r'(?<=[.!?]) +', text)
        words = [word for sentence in sentences for word in splitWordsBySize(sentence.split(), maxCaptionSize)]
    else:
        words = text.split()
        words = [cleanWord(word) for word in splitWordsBySize(words, maxCaptionSize)]
    
    for word in words:
        position += len(word) + 1
        end_time = interpolateTimeFromDict(position, wordLocationToTime)
        if end_time and word:
            CaptionsPairs.append(((start_time, end_time), word))
            start_time = end_time

    return CaptionsPairs
