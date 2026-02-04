# Voice Reference

Detailed documentation for Bulbul voices and voice selection.

## Female Voices

### Anushka
- **Tone:** Warm, friendly
- **Best for:** General purpose, greetings, conversational
- **Languages:** All supported languages

### Manisha
- **Tone:** Professional, clear
- **Best for:** Announcements, instructions, business
- **Languages:** All supported languages

### Vidya
- **Tone:** Energetic, upbeat
- **Best for:** Marketing, promotional content
- **Languages:** All supported languages

## Male Voices

### Arjun
- **Tone:** Authoritative, confident
- **Best for:** News, formal announcements
- **Languages:** All supported languages

### Amol
- **Tone:** Casual, warm
- **Best for:** Storytelling, informal content
- **Languages:** All supported languages

### Amartya
- **Tone:** Deep, mature
- **Best for:** Documentary, formal narration
- **Languages:** All supported languages

## Voice Selection by Use Case

| Use Case | Recommended Voice |
|----------|-------------------|
| Customer service | Anushka, Manisha |
| IVR systems | Manisha, Arjun |
| Audiobooks | Amol, Vidya |
| News reading | Arjun |
| Educational | Anushka, Amartya |
| Entertainment | Vidya, Amol |

## Voice Control Examples

### Slow and Clear (Educational)

```python
response = client.text_to_speech.convert(
    text="यह एक महत्वपूर्ण जानकारी है।",
    target_language_code="hi-IN",
    model="bulbul:v2",
    speaker="anushka",
    pace=0.8,
    pitch=0.0,
    loudness=1.2
)
```

### Fast and Energetic (Promotional)

```python
response = client.text_to_speech.convert(
    text="Limited time offer! Don't miss out!",
    target_language_code="en-IN",
    model="bulbul:v2",
    speaker="vidya",
    pace=1.3,
    pitch=0.2,
    loudness=1.5
)
```

### Deep and Formal (Documentary)

```python
response = client.text_to_speech.convert(
    text="In the annals of history...",
    target_language_code="en-IN",
    model="bulbul:v2",
    speaker="amartya",
    pace=0.9,
    pitch=-0.2,
    loudness=1.0
)
```

## Language-Voice Compatibility

All voices work with all supported languages. However, native speakers recommend:

| Language | Recommended Voice |
|----------|-------------------|
| Hindi | Anushka, Arjun |
| Tamil | Manisha, Amartya |
| Bengali | Vidya, Amol |
| Telugu | Anushka, Arjun |
| Kannada | Manisha, Amartya |

## Text Preprocessing

Bulbul automatically handles:

- **Numbers:** "100" → "one hundred" / "सौ"
- **Dates:** "15/08/1947" → "fifteenth August nineteen forty-seven"
- **Abbreviations:** Common ones expanded
- **Punctuation:** Natural pauses added

For explicit control, write text as you want it spoken:

```python
# Instead of
text = "The CEO met with 500 employees on 1/1/2024"

# Write
text = "The C E O met with five hundred employees on January first, twenty twenty-four"
```

