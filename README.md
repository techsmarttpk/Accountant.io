Accountant.io: Automated Income Tax Calculation and Query Assistance

Overview
We at Guns and Roses are delighted to introduce Accountant.io, which is a Telegram bot designed to simplify the process of calculating income tax for Indian citizens. It allows users to upload salary details or financial documents, manually calculates their tax, and provides GPT-2 powered responses to tax-related queries. The bot handles both text-based and audio input, and offers an intuitive experience for users with little to no tax knowledge.

Download the trained model here:
https://drive.google.com/drive/folders/1pKuT45QF0sgDgscIJ51WabAsvw7hPSeY?usp=sharing

Features
Manual Income Tax Calculation: Extracts financial details from user-provided text or documents (PDFs), and performs income tax calculations based on Indian tax laws.
Document and Audio Support: Accepts text inputs, PDFs, and audio messages to make tax filing accessible to everyone.
GPT-2 Powered Responses: Provides answers to tax-related questions using a fine-tuned GPT-2 model, focused on clearing doubts regarding deductions, exemptions, and tax laws.
Regex-Based Extraction: Extracts salary, income, deductions, and expenses using custom regex patterns.
Simple and Efficient: Built for simplicity, offering users a smooth, hassle-free tax filing experience via Telegram.
How It Works
Start the Bot: Use the /start command to initiate the bot.
Upload Your Documents: Send in your salary details via text or upload a document (PDF format).
Audio Support: Can't type? No problem! Send an audio message, and the bot will convert it into text and calculate your tax.
Tax Calculation: The bot calculates your taxable income by manually extracting income, expenses, and deductions from the provided details.
Ask a Question: Have tax-related questions? Ask the bot, and it will provide relevant answers using GPT-2.
Receive Results: Get your calculated tax or clarified doubts in a few moments.

Installation
Requirements
Python 3.10+
Telegram Bot Token (from BotFather)
PyMuPDF (for PDF processing)
SpeechRecognition (for audio handling)
HuggingFace Transformers (for GPT-2)

Once the bot is running, users can interact with it on Telegram. Use the /start command to begin, then either send text input or upload a document. The bot will calculate your tax manually and provide GPT-2 powered answers to any questions you might have.

Example Commands
/start: Initiates the bot and displays a welcome message.
Document Upload: Send your PDF, and the bot will process and calculate the tax based on the information.
Ask a Question: Type a question like "What is Section 80C?" to get an answer.
Audio Input: Send a voice message, and the bot will transcribe it and calculate your tax.
Tax Calculation Logic
Income Extraction: Regex-based extraction for various income sources such as salary, rental income, dividends, etc.
Deductions: Supports deductions under Section 80C, 80D, and more.
Expense Tracking: Extracts common expense patterns to calculate net taxable income.
Manual Calculation: Tax is calculated manually based on Indian tax slabs.
GPT-2 Integration
TaxBot uses a fine-tuned version of GPT-2 to answer user queries related to Indian income tax. It helps clarify doubts about deductions, exemptions, and tax rules, but tax calculations themselves are performed manually.

Limitations
GPT-2 for Queries: The GPT-2 model is used solely for answering questions and does not perform tax calculations.
Manual Tax Calculation: The actual tax computation is performed manually using financial details extracted from user input.
Indian Tax Laws: This bot currently supports tax laws applicable to Indian citizens.
