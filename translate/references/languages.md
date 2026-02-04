# Language Reference

Detailed information about supported languages and translation quality.

## Language Codes (BCP-47)

| Language | Code | Native Name | Script |
|----------|------|-------------|--------|
| Hindi | `hi-IN` | हिन्दी | Devanagari |
| Bengali | `bn-IN` | বাংলা | Bengali |
| Tamil | `ta-IN` | தமிழ் | Tamil |
| Telugu | `te-IN` | తెలుగు | Telugu |
| Kannada | `kn-IN` | ಕನ್ನಡ | Kannada |
| Malayalam | `ml-IN` | മലയാളം | Malayalam |
| Marathi | `mr-IN` | मराठी | Devanagari |
| Gujarati | `gu-IN` | ગુજરાતી | Gujarati |
| Punjabi | `pa-IN` | ਪੰਜਾਬੀ | Gurmukhi |
| Odia | `or-IN` | ଓଡ଼ିଆ | Odia |
| English | `en-IN` | English | Latin |

## Script Options

### Devanagari Languages
Languages that use Devanagari script:
- Hindi (`hi-IN`)
- Marathi (`mr-IN`)

Output scripts: `devanagari`, `latin`

### South Indian Languages
- Tamil (`ta-IN`) - Tamil script or `latin`
- Telugu (`te-IN`) - Telugu script or `latin`
- Kannada (`kn-IN`) - Kannada script or `latin`
- Malayalam (`ml-IN`) - Malayalam script or `latin`

### Eastern Languages
- Bengali (`bn-IN`) - Bengali script or `latin`
- Odia (`or-IN`) - Odia script or `latin`

### Western Languages
- Gujarati (`gu-IN`) - Gujarati script or `latin`

### Punjabi
- Punjabi (`pa-IN`) - Gurmukhi script or `latin`

## Translation Quality Notes

### High Quality Pairs
- English ↔ Hindi
- English ↔ Tamil
- English ↔ Bengali
- English ↔ Telugu

### Good Quality Pairs
- English ↔ Kannada
- English ↔ Malayalam
- English ↔ Marathi
- English ↔ Gujarati

### Developing
- English ↔ Punjabi
- English ↔ Odia
- Indian Language ↔ Indian Language (via English pivot)

## Domain-Specific Tips

### Technical Content
```python
# Technical terms may need context
response = client.translate.translate(
    input="Click the submit button to send the form",
    source_language_code="en-IN",
    target_language_code="hi-IN",
    mode="formal"  # Use formal for technical
)
```

### Conversational Content
```python
# Casual mode for chat/conversational
response = client.translate.translate(
    input="What's up? How's it going?",
    source_language_code="en-IN",
    target_language_code="hi-IN",
    mode="casual"
)
```

### Formal Documents
```python
# Formal mode for legal/business
response = client.translate.translate(
    input="Please find attached the contract for your review",
    source_language_code="en-IN",
    target_language_code="hi-IN",
    mode="formal"
)
```

## Common Issues

### Mixed Script Input
If input contains mixed scripts, use `auto` detection:
```python
response = client.translate.translate(
    input="मुझे coffee चाहिए",  # Mixed Hindi + English
    source_language_code="auto",
    target_language_code="en-IN"
)
```

### Proper Nouns
Proper nouns are generally preserved:
```python
response = client.translate.translate(
    input="Meet me at Starbucks in Delhi",
    source_language_code="en-IN",
    target_language_code="hi-IN"
)
# "दिल्ली में Starbucks पर मिलो"
```

### Numerical Data
Use `numeral_format` to control number representation:
```python
# For financial content, international is clearer
response = client.translate.translate(
    input="Total: ₹15,000",
    source_language_code="en-IN",
    target_language_code="hi-IN",
    numeral_format="international"
)
```

