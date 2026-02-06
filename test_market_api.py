#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import os

# Конфигурация
BASE_URL = "http://127.0.0.1:5000"
API_URL = f"{BASE_URL}/api"

class APITester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'APITester/2.1'
        })
        self.current_token = None
        self.current_user = None
        self.debug = False  # Включить отладку
        
    def decode_response(self, response):
        """Декодирует ответ с автоматическим определением кодировки"""
        if self.debug:
            print(f"\n[DEBUG] decode_response called")
            print(f"[DEBUG] Response encoding: {response.encoding}")
            print(f"[DEBUG] Content type: {response.headers.get('content-type')}")
            print(f"[DEBUG] Raw content first 200 bytes: {response.content[:200]}")
        
        try:
            # Пробуем разные кодировки
            encodings_to_try = ['utf-8', 'cp1251', 'iso-8859-1', 'windows-1251']
            
            for encoding in encodings_to_try:
                try:
                    decoded_text = response.content.decode(encoding)
                    if self.debug:
                        print(f"[DEBUG] Successfully decoded as {encoding}")
                        print(f"[DEBUG] Decoded text: {decoded_text[:200]}")
                    
                    # Пытаемся распарсить JSON
                    if 'application/json' in response.headers.get('content-type', ''):
                        try:
                            result = json.loads(decoded_text)
                            if self.debug:
                                print(f"[DEBUG] Successfully parsed JSON")
                            return result
                        except json.JSONDecodeError as e:
                            if self.debug:
                                print(f"[DEBUG] JSON parse error: {e}")
                            # Возвращаем текст как есть
                            return decoded_text
                    else:
                        return decoded_text
                        
                except UnicodeDecodeError:
                    continue
            
            # Если ни одна кодировка не сработала
            if self.debug:
                print(f"[DEBUG] Could not decode with any encoding")
            return response.text
            
        except Exception as e:
            if self.debug:
                print(f"[DEBUG] Exception in decode_response: {e}")
            return response.text
    
    def print_response(self, response):
        """Выводит ответ в читаемом формате"""
        if response is None:
            print("Не удалось выполнить запрос")
            return
        
        # Получаем метод запроса
        method = response.request.method if hasattr(response, 'request') and response.request else 'GET'
        
        # Получаем отправленные данные
        request_data = None
        if hasattr(response, 'request') and response.request:
            if response.request.body:
                try:
                    # Для JSON запросов
                    if 'application/json' in response.request.headers.get('Content-Type', ''):
                        request_data = json.loads(response.request.body)
                    # Для form-data (multipart)
                    elif 'multipart/form-data' in response.request.headers.get('Content-Type', ''):
                        # Извлекаем только текстовые поля из form-data
                        body_text = response.request.body.decode('utf-8', errors='ignore')
                        # Упрощенная обработка - показываем структуру без бинарных данных
                        if 'Content-Disposition: form-data' in body_text:
                            lines = body_text.split('\r\n')
                            text_fields = []
                            for line in lines:
                                if 'name="' in line and 'filename' not in line:
                                    # Извлекаем имя поля
                                    name_start = line.find('name="') + 6
                                    name_end = line.find('"', name_start)
                                    if name_end > name_start:
                                        field_name = line[name_start:name_end]
                                        # Ищем значение (обычно через 2 строки)
                                        try:
                                            line_index = lines.index(line)
                                            if line_index + 4 < len(lines):
                                                field_value = lines[line_index + 4]
                                                text_fields.append(f"{field_name}: {field_value}")
                                        except:
                                            pass
                            if text_fields:
                                request_data = "Form-data: " + ", ".join(text_fields)
                    # Для URL encoded
                    elif 'application/x-www-form-urlencoded' in response.request.headers.get('Content-Type', ''):
                        import urllib.parse
                        request_data = urllib.parse.parse_qs(response.request.body.decode('utf-8'))
                except:
                    # Если не удалось распарсить, показываем сырые данные (первые 500 байт)
                    try:
                        body_preview = str(response.request.body)[:500]
                        if len(body_preview) > 100:
                            request_data = f"Raw body (truncated): {body_preview[:100]}..."
                        else:
                            request_data = f"Raw body: {body_preview}"
                    except:
                        request_data = "Binary data or unreadable format"
        
        print(f"\n{'='*60}")
        print(f"Статус: {response.status_code}")
        print(f"URL ({method}): {response.url}")
        
        # Показываем отправленные данные
        if request_data:
            print(f"\nОтправленные данные ({method}):")
            if isinstance(request_data, dict):
                print(json.dumps(request_data, ensure_ascii=False, indent=2))
            else:
                print(request_data)
        
        if response.status_code != 200:
            print(f"Ошибка HTTP: {response.reason}")
        
        # Получаем и декодируем ответ
        result = self.decode_response(response)
        
        # Выводим результат
        print(f"\nПолученный ответ:")
        if isinstance(result, dict):
            print(json.dumps(result, ensure_ascii=False, indent=2))
        elif isinstance(result, list):
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(result)
        
        # Показываем дополнительные заголовки для отладки
        if self.debug:
            print(f"\n[DEBUG] Заголовки ответа:")
            for header, value in response.headers.items():
                if header.lower() not in ['date', 'server']:  # Пропускаем стандартные заголовки
                    print(f"  {header}: {value}")
            
            if hasattr(response, 'request') and response.request:
                print(f"\n[DEBUG] Заголовки запроса:")
                for header, value in response.request.headers.items():
                    if header.lower() not in ['user-agent', 'accept-encoding', 'connection']:
                        print(f"  {header}: {value}")
        
        print(f"{'='*60}\n")
        return result
    
    def clear_screen(self):
        """Очищает экран консоли"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def wait_for_input(self, message="Нажмите Enter для продолжения..."):
        """Ожидает ввода пользователя"""
        input(f"\n{message}")
    
    def test_health_check(self):
        """Тест health check эндпоинта"""
        print("\n1. Проверка здоровья сервера")
        print("-" * 30)
        response = self.make_request('GET', '/health')
        return self.print_response(response)
    
    def register(self):
        """Регистрация нового пользователя"""
        print("\n2. Регистрация нового пользователя")
        print("-" * 30)
        
        login = input("Логин: ").strip()
        mail = input("Email: ").strip()
        password = input("Пароль: ").strip()
        
        data = {
            'login': login,
            'mail': mail,
            'password': password
        }
        
        if self.debug:
            print(f"[DEBUG] Registration data: {data}")
        
        response = self.make_request('POST', '/auth/register', data)
        result = self.print_response(response)
        
        if response and response.status_code == 201:
            if isinstance(result, dict) and 'user' in result and 'tokens' in result:
                self.current_token = result['tokens'].get('access_token')
                self.current_user = result['user'].get('nickname')
                print(f"\n✓ Автоматически авторизован как: {self.current_user}")
                print(f"✓ Токен получен: {self.current_token}")
            else:
                print(f"\n✗ Не удалось получить токен из ответа")
                print(f"Ответ: {result}")
    
    def login(self):
        """Вход в систему"""
        print("\n3. Вход в систему")
        print("-" * 30)
        
        login = input("Логин: ").strip()
        password = input("Пароль: ").strip()
        
        data = {
            'login': login,
            'password': password
        }
        
        if self.debug:
            print(f"[DEBUG] Login data: {data}")
        
        response = self.make_request('POST', '/auth/login', data)
        result = self.print_response(response)
        
        if response and response.status_code == 200:
            if isinstance(result, dict) and 'user' in result and 'tokens' in result:
                self.current_token = result['tokens'].get('access_token')
                self.current_user = result['user'].get('nickname')
                print(f"\n✓ Успешно авторизован как: {self.current_user}")
                print(f"✓ Токен получен: {self.current_token}")
            else:
                print(f"\n✗ Не удалось получить токен из ответа")
                print(f"Структура ответа: {result}")
        else:
            print(f"\n✗ Ошибка входа. Статус: {response.status_code if response else 'No response'}")
    
    def refresh_token(self):
        """Обновление токена"""
        print("\n4. Обновление токена")
        print("-" * 30)
        
        if not self.current_token:
            print("Ошибка: Сначала выполните вход или регистрацию")
            return
        
        # В реальном приложении нужно хранить refresh_token
        refresh_token = input("Refresh token: ").strip()
        
        if not refresh_token:
            print("Ошибка: Refresh token обязателен")
            return
        
        data = {'refresh_token': refresh_token}
        response = self.make_request('POST', '/auth/refresh', data)
        result = self.print_response(response)
        
        if response and response.status_code == 200:
            if isinstance(result, dict) and 'access_token' in result:
                self.current_token = result['access_token']
                print(f"\n✓ Токен обновлен: {self.current_token}")
    
    def get_profile(self):
        """Получение профиля текущего пользователя"""
        print("\n5. Получение профиля пользователя")
        print("-" * 30)
        
        if not self.current_token:
            print("Ошибка: Сначала выполните вход или регистрацию")
            return
        
        is_active = input("Показать активные товары? (y/n, по умолчанию y): ").strip().lower()
        params = {'is_active': 'true' if is_active in ['y', ''] else 'false'}
        
        response = self.make_request('GET', '/auth/profile', params)
        self.print_response(response)
    
    def get_products(self):
        """Получение списка товаров"""
        print("\n6. Получение списка товаров")
        print("-" * 30)
        
        page = input("Номер страницы (по умолчанию 1): ").strip()
        page = int(page) if page.isdigit() else 1
        
        is_active = input("Показать активные товары? (y/n, по умолчанию y): ").strip().lower()
        
        params = {
            'page': page,
            'is_active': 'true' if is_active in ['y', ''] else 'false'
        }
        
        response = self.make_request('GET', '/products', params)
        self.print_response(response)
    
    def get_product_detail(self):
        """Получение детальной информации о товаре"""
        print("\n7. Получение детальной информации о товаре")
        print("-" * 30)
        
        product_id = input("ID товара: ").strip()
        
        if not product_id:
            print("Ошибка: ID товара обязателен")
            return
        
        response = self.make_request('GET', f'/products/{product_id}')
        self.print_response(response)
    
    def create_product_with_curl(self):
        """Создание товара через curl"""
        print("\n8. Создание товара")
        print("-" * 30)
        
        if not self.current_token:
            print("Ошибка: Сначала выполните вход или регистрацию")
            return
        
        print("Введите данные товара:")
        title = input("Название товара (3-100 символов): ").strip()
        price = input("Цена (1-10000 AC): ").strip()
        description = input("Описание (до 1000 символов, необязательно): ").strip()
        
        print("\nУкажите путь к изображению:")
        print("(можно перетащить файл в окно терминала)")
        image_path = input("Путь: ").strip().strip('"\'')
        
        if not all([title, price, image_path]):
            print("❌ Название, цена и изображение обязательны!")
            return
        
        if not os.path.exists(image_path):
            print(f"❌ Файл не найден: {image_path}")
            return
        
        try:
            # Формируем команду curl
            import subprocess
            
            # Базовые параметры curl
            cmd = [
                'curl', '-X', 'POST',
                f'{API_URL}/products',
                '-H', f'Authorization: Bearer {self.current_token}',
                '-F', f'title={title}',
                '-F', f'price={price}',
                '--silent'
            ]
            
            # Добавляем описание если есть
            if description:
                cmd.extend(['-F', f'description={description}'])
            
            # Добавляем файл изображения
            cmd.extend(['-F', f'image=@{image_path}'])
            
            print(f"\nВыполняем команду curl...")
            
            # Выполняем команду
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
            
            print(f"\nСтатус curl: {result.returncode}")
            
            if result.stdout:
                try:
                    response_data = json.loads(result.stdout)
                    print("\nОтвет от сервера:")
                    print(json.dumps(response_data, ensure_ascii=False, indent=2))
                except:
                    print(f"Ответ: {result.stdout}")
            
            if result.stderr:
                print(f"\nОшибка curl: {result.stderr}")
                
        except Exception as e:
            print(f"❌ Ошибка при выполнении curl: {e}")
    
    def update_product_price(self):
        """Изменение цены товара"""
        print("\n9. Изменение цены товара")
        print("-" * 30)
        
        if not self.current_token:
            print("Ошибка: Сначала выполните вход или регистрацию")
            return
        
        product_id = input("ID товара: ").strip()
        new_price = input("Новая цена: ").strip()
        
        if not product_id or not new_price:
            print("Ошибка: ID товара и новая цена обязательны")
            return
        
        try:
            new_price = int(new_price)
        except ValueError:
            print("Ошибка: Цена должна быть числом")
            return
        
        data = {'new_price': new_price}
        response = self.make_request('PUT', f'/products/{product_id}/price', data)
        self.print_response(response)
    
    def subscribe_to_product(self):
        """Подписка на товар"""
        print("\n10. Подписка на товар")
        print("-" * 30)
        
        if not self.current_token:
            print("Ошибка: Сначала выполните вход или регистрацию")
            return
        
        product_id = input("ID товара: ").strip()
        
        if not product_id:
            print("Ошибка: ID товара обязателен")
            return
        
        response = self.make_request('POST', f'/products/{product_id}/subscribe')
        self.print_response(response)
    
    def unsubscribe_from_product(self):
        """Отписка от товара"""
        print("\n11. Отписка от товара")
        print("-" * 30)
        
        if not self.current_token:
            print("Ошибка: Сначала выполните вход или регистрацию")
            return
        
        product_id = input("ID товара: ").strip()
        
        if not product_id:
            print("Ошибка: ID товара обязателен")
            return
        
        response = self.make_request('POST', f'/products/{product_id}/unsubscribe')
        self.print_response(response)
    
    def remove_product(self):
        """Снятие товара с продажи"""
        print("\n12. Снятие товара с продажи")
        print("-" * 30)
        
        if not self.current_token:
            print("Ошибка: Сначала выполните вход или регистрацию")
            return
        
        product_id = input("ID товара: ").strip()
        
        if not product_id:
            print("Ошибка: ID товара обязателен")
            return
        
        response = self.make_request('POST', f'/products/{product_id}/remove')
        self.print_response(response)
    
    def search_products(self):
        """Поиск товаров"""
        print("\n13. Поиск товаров")
        print("-" * 30)
        
        search_term = input("Поисковый запрос: ").strip()
        
        if not search_term:
            print("Ошибка: Поисковый запрос обязателен")
            return
        
        page = input("Номер страницы (по умолчанию 1): ").strip()
        page = int(page) if page.isdigit() else 1
        
        min_score = input("Минимальный порог релевантности (0-1, по умолчанию 0.1): ").strip()
        
        params = {
            'q': search_term,
            'page': page
        }
        
        try:
            if min_score:
                params['min_score'] = float(min_score)
        except ValueError:
            print("Предупреждение: Неверный формат min_score, используется значение по умолчанию")
        
        response = self.make_request('GET', '/products/search', params)
        self.print_response(response)
    
    def get_user_subscriptions(self):
        """Получение подписок пользователя"""
        print("\n14. Получение подписок пользователя")
        print("-" * 30)
        
        if not self.current_token:
            print("Ошибка: Сначала выполните вход или регистрацию")
            return
        
        is_active = input("Показать активные подписки? (y/n, по умолчанию y): ").strip().lower()
        params = {'is_active': 'true' if is_active in ['y', ''] else 'false'}
        
        response = self.make_request('GET', '/account/subscriptions', params)
        self.print_response(response)
    
    def declare_bankruptcy(self):
        """Объявление банкротства"""
        print("\n15. Объявление банкротства")
        print("-" * 30)
        
        if not self.current_token:
            print("Ошибка: Сначала выполните вход или регистрацию")
            return
        
        print(f"Текущий пользователь: {self.current_user}")
        print("Внимание: Банкротство можно объявлять только 1 раз до следующего обновления цен")
        print("и только при балансе < 100 AC, без активных товаров и подписок")
        
        confirm = input("Вы уверены? (y/n): ").strip().lower()
        
        if confirm != 'y':
            print("Отменено")
            return
        
        response = self.make_request('POST', '/account/bankruptcy')
        self.print_response(response)
    
    def get_toplist(self):
        """Получить список самых богатых игроков"""
        print("\n16. Получить список самых богатых игроков")
        print("-" * 30)

        page = input("Номер страницы (по умолчанию 1): ").strip()
        page = int(page) if page.isdigit() else 1
        
        per_page = input("Количество игроков на одной странице (1-100, по умолчанию 20): ").strip()
        per_page = int(per_page) if per_page.isdigit() else 20
        
        params = {
            'page': page,
            'per_page': min(max(per_page, 1), 100)  # Ограничение 1-100
        }
        
        response = self.make_request('GET', '/players/rating', params)
        self.print_response(response)
    
    def get_image(self):
        """Получение изображения товара"""
        print("\n17. Получение изображения товара")
        print("-" * 30)
        
        file_id = input("ID файла изображения: ").strip()
        
        if not file_id:
            print("Ошибка: ID файла обязателен")
            return
        
        url = f"{API_URL}/images/thumbnail/{file_id}"
        print(f"URL для просмотра в браузере: {url}")
        
        # Пытаемся скачать изображение
        try:
            response = requests.get(url, stream=True)
            if response.status_code == 200:
                print(f"✓ Изображение найдено, размер: {len(response.content)} байт")
                print(f"✓ Content-Type: {response.headers.get('content-type')}")
                
                # Сохраняем изображение
                save = input("Сохранить изображение? (y/n): ").strip().lower()
                if save == 'y':
                    filename = input("Имя файла для сохранения (по умолчанию image.jpg): ").strip()
                    if not filename:
                        filename = 'image.jpg'
                    
                    with open(filename, 'wb') as f:
                        f.write(response.content)
                    print(f"✓ Изображение сохранено как {filename}")
            else:
                print(f"✗ Ошибка: {response.status_code}")
                if response.headers.get('content-type') == 'application/json':
                    error = response.json()
                    print(f"Ошибка: {error.get('error', 'Неизвестная ошибка')}")
        except Exception as e:
            print(f"✗ Ошибка при загрузке изображения: {e}")
    
    def logout(self):
        """Выход из системы"""
        print("\n18. Выход из системы")
        print("-" * 30)
        
        self.current_token = None
        self.current_user = None
        print("✓ Успешно вышли из системы")
    
    def show_status(self):
        """Показывает текущий статус"""
        print("\nТекущий статус:")
        print("-" * 30)
        if self.current_user:
            print(f"Авторизован как: {self.current_user}")
            print(f"Токен: {self.current_token[:20]}..." if self.current_token and len(self.current_token) > 20 else f"Токен: {self.current_token}")
        else:
            print("Не авторизован")
        print(f"Сервер: {BASE_URL}")
        print(f"API версия: 2.1")
    
    def make_request(self, method, endpoint, data=None, headers=None, files=None):
        """Выполняет HTTP запрос с обработкой ошибок"""
        url = f"{API_URL}{endpoint}"
        
        # Добавляем токен авторизации, если есть
        request_headers = {}
        if headers:
            request_headers.update(headers)
        
        if self.current_token and 'Authorization' not in request_headers:
            request_headers['Authorization'] = f'Bearer {self.current_token}'
            if self.debug:
                print(f"[DEBUG] Adding Authorization header with token: {self.current_token[:20]}...")
        
        # Сохраняем данные для отображения
        sent_data = data
        
        if self.debug:
            print(f"[DEBUG] Making {method} request to {url}")
            print(f"[DEBUG] Headers: {request_headers}")
            if data and not files:
                print(f"[DEBUG] Data to send: {data}")
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, params=data, headers=request_headers)
                # Для GET запросов данные в params
                response._sent_data = data
                response._method = 'GET'
                
            elif method.upper() == 'POST':
                if files:
                    # Сохраняем данные формы отдельно
                    response = self.session.post(url, data=data, files=files, headers=request_headers)
                    response._sent_data = data
                    response._method = 'POST'
                else:
                    response = self.session.post(url, json=data, headers=request_headers)
                    response._sent_data = data
                    response._method = 'POST'
                    
            elif method.upper() == 'PUT':
                response = self.session.put(url, json=data, headers=request_headers)
                response._sent_data = data
                response._method = 'PUT'
                
            elif method.upper() == 'DELETE':
                response = self.session.delete(url, headers=request_headers)
                response._sent_data = None  # DELETE обычно без тела
                response._method = 'DELETE'
                
            else:
                raise ValueError(f"Неподдерживаемый метод: {method}")
            
            # Добавляем метод в объект ответа для удобного доступа
            response._method = method.upper()
            
            if self.debug:
                print(f"[DEBUG] Response status: {response.status_code}")
                print(f"[DEBUG] Response headers: {dict(response.headers)}")
            
            return response
            
        except requests.exceptions.ConnectionError:
            print("Ошибка: Не удалось подключиться к серверу. Убедитесь, что сервер запущен.")
            return None
        except Exception as e:
            print(f"Ошибка запроса: {e}")
            return None
    
    def test_raw_request(self):
        """Прямой запрос для отладки"""
        print("\n19. Прямой запрос (для отладки)")
        print("-" * 30)
        
        method = input("Метод (GET/POST/PUT/DELETE): ").strip().upper()
        endpoint = input("Эндпоинт (например: /auth/login): ").strip()
        
        if method in ['POST', 'PUT']:
            data_str = input("Данные JSON (необязательно): ").strip()
            data = json.loads(data_str) if data_str else {}
        else:
            data = None
        
        response = self.make_request(method, endpoint, data)
        self.print_response(response)
    
    def main_menu(self):
        """Главное меню"""
        while True:
            self.clear_screen()
            print("=" * 60)
            print("API ТЕСТЕР ДЛЯ МАРКЕТПЛЕЙСА v2.1")
            print("=" * 60)
            
            self.show_status()
            
            print("\nВыберите действие:")
            print("=" * 60)
            print(" 1. Проверка здоровья сервера")
            print(" 2. Регистрация")
            print(" 3. Вход")
            print(" 4. Обновить токен")
            print(" 5. Получить профиль")
            print(" 6. Получить список товаров")
            print(" 7. Получить детали товара")
            print(" 8. Создать товар")
            print(" 9. Изменить цену товара")
            print("10. Подписаться на товар")
            print("11. Отписаться от товара")
            print("12. Снять товар с продажи")
            print("13. Поиск товаров")
            print("14. Мои подписки")
            print("15. Объявить банкротство")
            print("16. Самые богатые игроки")
            print("17. Получить изображение")
            print("18. Выйти из системы")
            print("19. Прямой запрос (отладка)")
            print(" 0. Выход из программы")
            print("=" * 60)
            
            choice = input("\nВаш выбор (0-19): ").strip()
            
            if choice == '0':
                print("\nДо свидания!")
                break
            elif choice == '1':
                self.test_health_check()
                self.wait_for_input()
            elif choice == '2':
                self.register()
                self.wait_for_input()
            elif choice == '3':
                self.login()
                self.wait_for_input()
            elif choice == '4':
                self.refresh_token()
                self.wait_for_input()
            elif choice == '5':
                self.get_profile()
                self.wait_for_input()
            elif choice == '6':
                self.get_products()
                self.wait_for_input()
            elif choice == '7':
                self.get_product_detail()
                self.wait_for_input()
            elif choice == '8':
                self.create_product_with_curl()
                self.wait_for_input()
            elif choice == '9':
                self.update_product_price()
                self.wait_for_input()
            elif choice == '10':
                self.subscribe_to_product()
                self.wait_for_input()
            elif choice == '11':
                self.unsubscribe_from_product()
                self.wait_for_input()
            elif choice == '12':
                self.remove_product()
                self.wait_for_input()
            elif choice == '13':
                self.search_products()
                self.wait_for_input()
            elif choice == '14':
                self.get_user_subscriptions()
                self.wait_for_input()
            elif choice == '15':
                self.declare_bankruptcy()
                self.wait_for_input()
            elif choice == '16':
                self.get_toplist()
                self.wait_for_input()
            elif choice == '17':
                self.get_image()
                self.wait_for_input()
            elif choice == '18':
                self.logout()
                self.wait_for_input()
            elif choice == '19':
                self.test_raw_request()
                self.wait_for_input()
            else:
                print("\nНеверный выбор. Попробуйте снова.")
                self.wait_for_input()

def main():
    """Точка входа в программу"""
    print("Запуск API тестера для Market API v2.1...")
    print(f"Подключение к серверу: {BASE_URL}")
    
    tester = APITester()
    
    # Проверяем доступность сервера
    print("\nПроверка подключения к серверу...")
    try:
        response = tester.make_request('GET', '/health')
        if response:
            print(f"✓ Сервер ответил: {response.status_code}")
            result = tester.decode_response(response)
            if isinstance(result, dict) and result.get('status') == 'healthy':
                print(f"✓ Сервер работает корректно (версия: {result.get('version', 'unknown')})")
            else:
                print("⚠ Сервер отвечает, но ответ не соответствует ожидаемому формату")
                print(f"Ответ: {result}")
        else:
            print("✗ Сервер не ответил")
    except Exception as e:
        print(f"✗ Ошибка подключения: {e}")
    
    tester.wait_for_input("Нажмите Enter для продолжения в главное меню...")
    tester.main_menu()

if __name__ == "__main__":
    main()
