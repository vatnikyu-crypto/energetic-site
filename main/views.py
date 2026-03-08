import pandas as pd
import os
from datetime import datetime, date
from dateutil.relativedelta import relativedelta # Нужно установить: pip install python-dateutil
from django.shortcuts import render
from django.conf import settings
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages # Для уведомлений
from django.shortcuts import render, redirect # Добавь redirect в импорт
from bs4 import BeautifulSoup # Не забудь импортировать!
from django.core.paginator import Paginator

def education(request):
    return render(request, 'main/education.html')

def custom_page_not_found(request, exception):
    return render(request, 'main/404.html', status=404)

def about(request):
    return render(request, 'main/about.html')

def reviews_view(request):
    reviews_list = [
        {
            'company': 'ПАО «Россети Томск»',
            'date': '2025 г.',
            'preview_url': '/static/main/img/reviews/scan1.jpg', 
            'pdf_url': '/static/main/img/reviews/scan1.pdf'      
        },
        {
            'company': 'АО «Томская Генерация»',
            'date': '2025 г.',
            'preview_url': '/static/main/img/reviews/scan2.jpg',
            'pdf_url': '/static/main/img/reviews/scan2.pdf'
        },
        {
            'company': 'АО «Томск РТС»',
            'date': '2026 г.',
            'preview_url': '/static/main/img/reviews/scan3.jpg',
            'pdf_url': '/static/main/img/reviews/scan3.pdf'
        },
    ]
    return render(request, 'main/reviews.html', {'reviews': reviews_list})

def prices(request):
    excel_path = os.path.join(settings.BASE_DIR, 'main', 'data', 'prices.xlsx')
    categories = {}
    
    try:
        if os.path.exists(excel_path):
            df = pd.read_excel(excel_path)
            # 1. Группируем данные по категориям
            for category, group in df.groupby('Категория'):
                items = group.to_dict('records')
                
                # --- МАГИЯ ФОРМАТИРОВАНИЯ ТУТ ---
                for item in items:
                    try:
                        # Превращаем число 22600 в "22 600"
                        val = int(item['Стоимость'])
                        item['Стоимость'] = f"{val:,}".replace(',', ' ')
                    except:
                        # Если вдруг в ячейке текст вместо числа, оставляем как есть
                        pass
                # --------------------------------
                
                categories[category] = items
    except Exception as e:
        print(f"Ошибка чтения цен: {e}")

    return render(request, 'main/prices.html', {'categories': categories})



def contacts(request):
    return render(request, 'main/contacts.html')



def news_list(request):
    news_dir = os.path.join(settings.BASE_DIR, 'main', 'templates', 'main', 'news', 'items')
    img_dir = os.path.join(settings.BASE_DIR, 'main', 'static', 'main', 'img', 'news')
    
    all_news_items = []
    
    if os.path.exists(news_dir):
        files = [f for f in os.listdir(news_dir) if f.endswith('.html')]
        # Сортируем файлы (самые новые по дате изменения файла будут первыми)
        files.sort(key=lambda x: os.path.getmtime(os.path.join(news_dir, x)), reverse=True)

        for filename in files:
            slug = filename.replace('.html', '')
            file_path = os.path.join(news_dir, filename)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                soup = BeautifulSoup(content, 'html.parser')
                title_tag = soup.find(id='meta-title')
                date_tag = soup.find(id='meta-date')
                
                title = title_tag.get_text() if title_tag else slug.replace('-', ' ').capitalize()
                date = date_tag.get_text() if date_tag else "Дата не указана"

            found_img = None
            for ext in ['.jpg', '.jpeg', '.png', '.webp', '.JPG', '.PNG']:
                if os.path.exists(os.path.join(img_dir, f"{slug}{ext}")):
                    found_img = f"main/img/news/{slug}{ext}"
                    break
            
            all_news_items.append({
                'slug': slug,
                'title': title,
                'date': date,
                'image_path': found_img
            })

    # ЛОГИКА ПАГИНАЦИИ
    paginator = Paginator(all_news_items, 9) # По 9 новостей на страницу
    page_number = request.GET.get('page') # Получаем номер страницы из URL (?page=2)
    page_obj = paginator.get_page(page_number) # Получаем объекты для конкретной страницы

    return render(request, 'main/news/news_list.html', {'page_obj': page_obj})

def news_detail(request, slug):
    return render(request, f'main/news/items/{slug}.html')

def index(request):
    # 1. Получаем месяц и год из запроса или берем текущие
    try:
        req_month = int(request.GET.get('month', datetime.now().month))
        req_year = int(request.GET.get('year', datetime.now().year))
        target_date = date(req_year, req_month, 1)
    except:
        target_date = date.today().replace(day=1)

    # 2. Вычисляем даты для кнопок "Назад" и "Вперед"
    prev_date = target_date - relativedelta(months=1)
    next_date = target_date + relativedelta(months=1)

    # 3. Путь к файлу и название листа
    excel_path = os.path.join(settings.BASE_DIR, 'main', 'data', 'schedule.xlsx')
    months_ru = {
        1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель", 5: "Май", 6: "Июнь",
        7: "Июль", 8: "Август", 9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"
    }
    sheet_name = f"{months_ru[target_date.month]} {target_date.year}"

    courses = []
    try:
        if os.path.exists(excel_path):
            df = pd.read_excel(excel_path, sheet_name=sheet_name)
            df = df.dropna(subset=['Название'])
            courses = df.to_dict('records')
    except Exception as e:
        print(f"Лист {sheet_name} не найден")


    if request.method == 'POST':
        honeypot = request.POST.get('website_url')
        if honeypot:
            # Если поле заполнено, просто возвращаем страницу без отправки письма
            return redirect('index')
        
        

        name = request.POST.get('name')
        contact = request.POST.get('contact')
        
        # Формируем текст письма
        subject = f'Новая заявка на звонок: {name}'
        message = f'Имя клиента: {name}\nКонтактные данные: {contact}'
        
        try:
            send_mail(subject, message, settings.EMAIL_HOST_USER, [settings.EMAIL_HOST_USER])
            messages.success(request, 'Заявка успешно отправлена!')
            # МАГИЯ ТУТ: после успеха перенаправляем пользователя на чистую страницу
            return redirect('index') 
        except Exception as e:
            messages.error(request, 'Ошибка при отправке.')
            return redirect('index') # И тут тоже, чтобы не было дублей
        
    # --- ЛОГИКА ДЛЯ ПОСЛЕДНЕЙ НОВОСТИ ---
    news_dir = os.path.join(settings.BASE_DIR, 'main', 'templates', 'main', 'news', 'items')
    img_dir = os.path.join(settings.BASE_DIR, 'main', 'static', 'main', 'img', 'news')
    latest_news = None

    if os.path.exists(news_dir):
        files = [f for f in os.listdir(news_dir) if f.endswith('.html')]
        
        # Собираем данные, чтобы отсортировать их корректно
        temp_news_list = []
        for filename in files:
            slug = filename.replace('.html', '')
            file_path = os.path.join(news_dir, filename)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                soup = BeautifulSoup(content, 'html.parser')
                title_tag = soup.find(id='meta-title')
                date_tag = soup.find(id='meta-date')
                
                title = title_tag.get_text() if title_tag else slug
                raw_date = date_tag.get_text() if date_tag else "01.01.2000"
                
                # Для надежной сортировки пробуем парсить дату
                try:
                    dt = datetime.strptime(raw_date, '%d.%m.%Y')
                except:
                    dt = datetime.min

                # Ищем картинку
                found_img = None
                for ext in ['.jpg', '.jpeg', '.png', '.webp', '.JPG']:
                    if os.path.exists(os.path.join(img_dir, f"{slug}{ext}")):
                        found_img = f"main/img/news/{slug}{ext}"
                        break
                
                temp_news_list.append({
                    'slug': slug,
                    'title': title,
                    'date': raw_date,
                    'dt': dt,
                    'image': found_img
                })
        
        # Сортируем по дате и берем первую
        if temp_news_list:
            temp_news_list.sort(key=lambda x: x['dt'], reverse=True)
            latest_news = temp_news_list[0]

    return render(request, 'main/index.html', {
        'courses': courses,
        'current_month': sheet_name,
        'prev_month': prev_date.month,
        'prev_year': prev_date.year,
        'next_month': next_date.month,
        'next_year': next_date.year,
        'latest_news': latest_news,
    })

    