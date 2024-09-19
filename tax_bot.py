from telegram.ext import Application, CommandHandler, MessageHandler, filters
import fitz 
from transformers import GPT2LMHeadModel, GPT2Tokenizer
from telegram import Update
from telegram.ext import ContextTypes
import re
import speech_recognition as sr  

model_path = 'D:/Projects/Bots/python-telegram-bot/trained_gpt2'
tokenizer_path = 'D:/Projects/Bots/python-telegram-bot/trained_gpt2'

model = GPT2LMHeadModel.from_pretrained(model_path)
tokenizer = GPT2Tokenizer.from_pretrained(tokenizer_path)

async def start(update, context):
    await update.message.reply_text('Send me your salary details or upload a document for tax calculation.')


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document
    if document:
        file = await document.get_file()  
        await file.download_to_drive('user_input.pdf') 
        await update.message.reply_text("File downloaded successfully. Processing...")
        extracted_text = extract_text_from_pdf('user_input.pdf')
        tax_result = calculate_tax(extracted_text)
        await update.message.reply_text(tax_result)

async def handle_text(update, context):
    user_text = update.message.text
    tax_result = calculate_tax(user_text)
    await update.message.reply_text(tax_result)

async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    audio = update.message.audio
    if audio:
        file = await audio.get_file() 
        await file.download_to_drive('user_audio.ogg') 
        await update.message.reply_text("Audio downloaded successfully. Processing...")
        audio_text = convert_audio_to_text('user_audio.ogg')
        tax_result = calculate_tax(audio_text)
        await update.message.reply_text(tax_result)

def convert_audio_to_text(audio_path):
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_path) as source:
        audio = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio)
        except sr.UnknownValueError:
            return "Sorry, I could not understand the audio."
        except sr.RequestError:
            return "Sorry, there was an error with the audio recognition service."
    return text

def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def calculate_tax(text):
    try:
        total_income, total_expenses, total_deductions = extract_financial_details(text)
        
        net_income = total_income - total_expenses
        
        taxable_income = net_income - total_deductions
        
        tax = compute_income_tax(taxable_income)
        
        return f"Your estimated tax is: ₹{tax:.2f}"
    except Exception as e:
        return f"Could not extract or calculate tax from the provided document or text. Error: {str(e)}"

def extract_financial_details(text):
    income = 0
    expenses = 0
    deductions = 0

    income_patterns = {
        'Salary': re.compile(r'Salary\s*:\s*₹?([\d,]+)'),
        'Rental Income': re.compile(r'Rental Income\s*:\s*₹?([\d,]+)'),
        'Interest Income': re.compile(r'Interest Income\s*:\s*₹?([\d,]+)'),
        'Dividends': re.compile(r'Dividends\s*:\s*₹?([\d,]+)'),
        'Capital Gains': re.compile(r'Capital Gains\s*:\s*₹?([\d,]+)'),
        'Business Income': re.compile(r'Business Income\s*:\s*₹?([\d,]+)'),
        'Freelance Income': re.compile(r'Freelance Income\s*:\s*₹?([\d,]+)'),
        'Pension Income': re.compile(r'Pension Income\s*:\s*₹?([\d,]+)'),
    }

    deduction_patterns = {
        '80C': re.compile(r'80C\s*:\s*₹?([\d,]+)'),
        '80D': re.compile(r'80D\s*:\s*₹?([\d,]+)'),
        '80E': re.compile(r'80E\s*:\s*₹?([\d,]+)'),
        '24(b)': re.compile(r'24\(b\)\s*:\s*₹?([\d,]+)'),
        '80G': re.compile(r'80G\s*:\s*₹?([\d,]+)'),
    }

    expense_patterns = {
        'Rent Paid': re.compile(r'Rent Paid\s*:\s*₹?([\d,]+)'),
        'Utilities': re.compile(r'Utilities\s*:\s*₹?([\d,]+)'),
        'Office Rent': re.compile(r'Office Rent\s*:\s*₹?([\d,]+)'),
        'Internet and Phone Bills': re.compile(r'Internet and Phone Bills\s*:\s*₹?([\d,]+)'),
        'Medical Expenses': re.compile(r'Medical Expenses\s*:\s*₹?([\d,]+)'),
        'Travel Expenses': re.compile(r'Travel Expenses\s*:\s*₹?([\d,]+)'),
        'Home Renovation': re.compile(r'Home Renovation\s*:\s*₹?([\d,]+)'),
        'Charitable Donations': re.compile(r'Charitable Donations\s*:\s*₹?([\d,]+)'),
        'Business Expenses': re.compile(r'Business Expenses\s*:\s*₹?([\d,]+)'),
    }

    for key, pattern in income_patterns.items():
        match = pattern.search(text)
        if match:
            income += int(match.group(1).replace(',', ''))

    for key, pattern in deduction_patterns.items():
        match = pattern.search(text)
        if match:
            deductions += int(match.group(1).replace(',', ''))

    for key, pattern in expense_patterns.items():
        match = pattern.search(text)
        if match:
            expenses += int(match.group(1).replace(',', ''))

    return income, expenses, deductions

def compute_income_tax(taxable_income):
    if taxable_income <= 250000:
        return 0
    elif taxable_income <= 500000:
        return (taxable_income - 250000) * 0.05
    elif taxable_income <= 1000000:
        return 12500 + (taxable_income - 500000) * 0.2
    else:
        return 112500 + (taxable_income - 1000000) * 0.3

def answer_tax_questions(query):
    inputs = tokenizer.encode(query, return_tensors="pt")
    outputs = model.generate(inputs, max_length=100, num_return_sequences=1)
    return tokenizer.decode(outputs[0], skip_special_tokens=True)

async def handle_gpt_question(update, context):
    user_question = update.message.text
    print(f"Received GPT question: {user_question}")  
    response = answer_tax_questions(user_question)
    print(f"GPT response: {response}")
    await update.message.reply_text(response)

def main():
    application = Application.builder().token("6596002194:AAGftCJ2Pq_VE6HgKnZQx6rLk-mOFnAOTIo").build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'^(?!.*(Tax:|Income|Deductions|Expenses)).*'), handle_gpt_question))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text)) 
    application.add_handler(MessageHandler(filters.AUDIO, handle_audio)) 
    application.run_polling()

if __name__ == '__main__':
    main()
