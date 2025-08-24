# Simplified thalassemia info chatbot for ClotSync
import re

# Predefined responses for common questions
FAQ_RESPONSES = {
    'what is thalassemia': 'Thalassemia is a genetic blood disorder where the body makes less hemoglobin than normal. This can lead to anemia and other health problems. Regular blood transfusions are often needed to manage the condition.',
    
    'blood donation': 'Blood donation is a safe and simple process that can save up to 3 lives. Donors must be healthy, 18-65 years old, weigh at least 50kg, and have adequate hemoglobin levels.',
    
    'eligibility': 'To donate blood, you must be 18-65 years old, weigh at least 50kg, be in good health, and not have donated in the last 3-4 months (depending on gender).',
    
    'how often': 'Males can donate every 4 months (120 days), females every 3 months (90 days). This ensures your body has enough time to replenish blood cells.',
    
    'safe': 'Yes, blood donation is very safe! We use sterile, single-use equipment. The process takes about 10-15 minutes and you can resume normal activities the same day.',
    
    'process': 'The donation process: 1) Registration and health check, 2) Brief medical screening, 3) Blood collection (10-15 minutes), 4) Rest and refreshments, 5) You\'re done!',
    
    'recovery': 'Most people feel fine after donating. Drink plenty of fluids, avoid heavy exercise for 24 hours, and eat iron-rich foods. Your body replaces the lost blood within 4-8 weeks.',
    
    'why donate': 'Blood donations save lives every day! One donation can help up to 3 patients. Blood is needed for surgeries, cancer treatment, trauma care, and managing conditions like thalassemia.',
    
    'blood groups': 'The main blood groups are A, B, AB, and O, each with positive or negative Rh factor. O-negative is the universal donor, while AB-positive is the universal recipient.',
    
    'compatibility': 'O-negative can donate to anyone, A can donate to A and AB, B can donate to B and AB, AB can donate only to AB. Rh-negative can donate to both Rh-positive and Rh-negative.',
    
    'symptoms': 'Thalassemia symptoms include fatigue, weakness, pale skin, slow growth, bone problems, and frequent infections. Severity varies from mild to life-threatening.',
    
    'treatment': 'Thalassemia treatment includes regular blood transfusions, iron chelation therapy to remove excess iron, and sometimes bone marrow transplants. Early diagnosis and treatment are crucial.',
    
    'prevention': 'Thalassemia is genetic, so it cannot be prevented. However, genetic counseling can help families understand risks, and prenatal testing can detect the condition early.',
    
    'help': 'I can help with questions about thalassemia, blood donation eligibility, the donation process, blood types, and general health information. What would you like to know?',
    
    'hello': 'Hello! I\'m your ClotSync assistant. I can help you with information about thalassemia and blood donation. How can I assist you today?',
    
    'hi': 'Hi there! I\'m here to help with thalassemia and blood donation questions. What would you like to learn about?',
    
    'thanks': 'You\'re welcome! Feel free to ask more questions about thalassemia or blood donation. I\'m here to help!',
    
    'thank you': 'You\'re welcome! Feel free to ask more questions about thalassemia or blood donation. I\'m here to help!'
}

def handle_message(message, history=None):
    """Handle chatbot messages and return appropriate responses"""
    if not message:
        return "Please enter a message."
    
    # Convert to lowercase for better matching
    message_lower = message.lower().strip()
    
    # Check for exact matches first
    for key, response in FAQ_RESPONSES.items():
        if key in message_lower:
            return response
    
    # Check for partial matches
    for key, response in FAQ_RESPONSES.items():
        if any(word in message_lower for word in key.split()):
            return response
    
    # Check for common question patterns
    if any(word in message_lower for word in ['what', 'how', 'why', 'when', 'where', 'who']):
        if 'thalassemia' in message_lower:
            return FAQ_RESPONSES['what is thalassemia']
        elif 'donate' in message_lower or 'donation' in message_lower:
            return FAQ_RESPONSES['blood donation']
        elif 'eligible' in message_lower or 'eligibility' in message_lower:
            return FAQ_RESPONSES['eligibility']
        elif 'safe' in message_lower or 'dangerous' in message_lower:
            return FAQ_RESPONSES['safe']
        elif 'process' in message_lower or 'procedure' in message_lower:
            return FAQ_RESPONSES['process']
        elif 'recovery' in message_lower or 'recover' in message_lower:
            return FAQ_RESPONSES['recovery']
        elif 'blood group' in message_lower or 'blood type' in message_lower:
            return FAQ_RESPONSES['blood groups']
        elif 'compatible' in message_lower or 'compatibility' in message_lower:
            return FAQ_RESPONSES['compatibility']
        elif 'symptom' in message_lower or 'sign' in message_lower:
            return FAQ_RESPONSES['symptoms']
        elif 'treat' in message_lower or 'cure' in message_lower:
            return FAQ_RESPONSES['treatment']
        elif 'prevent' in message_lower or 'avoid' in message_lower:
            return FAQ_RESPONSES['prevention']
    
    # Default response for unrecognized questions
    return ("I'm not sure about that specific question. I can help with thalassemia information, blood donation eligibility, the donation process, blood types, and general health questions. Try asking about one of these topics!")


