import logging
import re
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# التوكن الخاص بك
TOKEN = "7699469441:AAEL8lTD6zdBdP0nAH9Pm8wa2YazDaaIKL8"

# إعداد السجلات لمتابعة الأخطاء
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "مرحباً! أنا بوت إنشاء الاستفتاءات 🗳\n\n"
        "أرسل الاستفتاءات بالشكل التالي:\n"
        "السؤال؟\nالخيار 1\nالخيار 2\n\n"
        "للإجابة الصحيحة ضع ✅ بجوار الخيار.\n"
        "لجعل التصويت غير مخفي اكتب 'عادي' أو 'visible' في آخر سطر."
    )
    await update.message.reply_text(welcome_text)

async def create_poll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not text:
        return

    # تقسيم النص بناءً على سطرين فارغين لدعم إرسال عدة استفتاءات في رسالة واحدة
    blocks = text.strip().split('\n\n')

    for block in blocks:
        lines = [line.strip() for line in block.split('\n') if line.strip()]
        
        if len(lines) < 3:
            continue  # تخطي إذا لم يكن هناك سؤال وخيارين على الأقل

        question = lines[0]
        raw_options = lines[1:]
        
        options = []
        is_anonymous = True
        poll_type = "regular"
        correct_option_id = None
        
        # 1. التحقق مما إذا كان التصويت "عادي" (غير مخفي)
        last_line_lower = raw_options[-1].lower()
        if last_line_lower in ['عادي', 'ظاهر', 'visible', 'public']:
            is_anonymous = False
            raw_options.pop() # إزالة سطر الأمر

        # 2. التحقق من نمط الإجابة في سطر منفصل (Answer: ...)
        answer_text = None
        if raw_options and (raw_options[-1].lower().startswith('answer:') or raw_options[-1].startswith('الاجابة:') or raw_options[-1].lower().startswith('answer :')):
            ans_line = raw_options.pop()
            # استخراج نص الإجابة بعد النقطتين
            if ':' in ans_line:
                answer_text = ans_line.split(':', 1)[1].strip().lower()
            poll_type = "quiz"

        # 3. معالجة الخيارات والبحث عن علامة ✅
        final_options = []
        for index, opt in enumerate(raw_options):
            clean_opt = opt
            
            # الحالة الأولى: علامة صح بجانب الخيار
            if '✅' in opt:
                poll_type = "quiz"
                correct_option_id = index
                clean_opt = opt.replace('✅', '').strip()
            
            final_options.append(clean_opt)

        # الحالة الثانية: مطابقة نص الإجابة المستخرج من سطر Answer
        if poll_type == "quiz" and correct_option_id is None and answer_text:
            for index, opt in enumerate(final_options):
                # نحاول مطابقة بداية الخيار (مثل a) ) أو النص كاملاً
                # مثال: Answer: c) Promoting... سيطابق الخيار الذي يبدأ بـ c)
                opt_lower = opt.lower()
                
                # تنظيف النص للمقارنة (إزالة الرموز الزائدة)
                if answer_text in opt_lower or (answer_text.split(')')[0] in opt_lower.split(')')[0] and len(answer_text) < 4):
                    correct_option_id = index
                    break
        
        # حماية من الأخطاء: إذا كان اختبار ولا يوجد إجابة محددة، حوله لعادي
        if poll_type == "quiz" and correct_option_id is None:
            poll_type = "regular"

        # التأكد من عدم تجاوز الحد الأقصى للخيارات (تيلجرام يسمح بـ 10)
        if len(final_options) > 10:
            final_options = final_options[:10]

        try:
            await context.bot.send_poll(
                chat_id=update.effective_chat.id,
                question=question,
                options=final_options,
                is_anonymous=is_anonymous,
                type=poll_type,
                correct_option_id=correct_option_id,
                explanation="الإجابة الصحيحة" if poll_type == "quiz" else None
            )
        except Exception as e:
            await update.message.reply_text(f"حدث خطأ في إنشاء الاستفتاء: {question}\nالسبب: {str(e)}")

if __name__ == '__main__':
    application = ApplicationBuilder().token(TOKEN).build()
    
    start_handler = CommandHandler('start', start)
    message_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), create_poll)
    
    application.add_handler(start_handler)
    application.add_handler(message_handler)
    
    print("Bot is running...")
    application.run_polling()