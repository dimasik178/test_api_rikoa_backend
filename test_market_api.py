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
            'User-Agent': 'APITester/1.0'
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
            
        print(f"\n{'='*60}")
        print(f"Статус: {response.status_code}")
        print(f"URL: {response.url}")
        
        if response.status_code != 200:
            print(f"Ошибка HTTP: {response.reason}")
        
        # Получаем и декодируем ответ
        result = self.decode_response(response)
        
        # Выводим результат
        if isinstance(result, dict):
            print("\nОтвет JSON:")
            print(json.dumps(result, ensure_ascii=False, indent=2))
        elif isinstance(result, list):
            print("\nОтвет (список):")
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print("\nОтвет:")
            print(result)
        
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
            if isinstance(result, dict) and result.get('success'):
                self.current_token = result['data']['tokens'].get('access_token')
                self.current_user = result['data']['user'].get('nickname')
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
            if isinstance(result, dict) and result.get('success'):
                self.current_token = result['data']['tokens'].get('access_token')
                self.current_user = result['data']['user'].get('nickname')
                print(f"\n✓ Успешно авторизован как: {self.current_user}")
                print(f"✓ Токен получен: {self.current_token}")
            else:
                print(f"\n✗ Не удалось получить токен из ответа")
                print(f"Структура ответа: {result}")
        else:
            print(f"\n✗ Ошибка входа. Статус: {response.status_code if response else 'No response'}")
    
    def get_profile(self):
        """Получение профиля текущего пользователя"""
        print("\n4. Получение профиля пользователя")
        print("-" * 30)
        
        if not self.current_token:
            print("Ошибка: Сначала выполните вход или регистрацию")
            print(f"Текущий токен: {self.current_token}")
            return
        
        print(f"Используется токен: {self.current_token}")
        response = self.make_request('GET', '/auth/profile')
        self.print_response(response)
    
    def get_products(self):
        """Получение списка товаров"""
        print("\n5. Получение списка товаров")
        print("-" * 30)
        
        page = input("Номер страницы (по умолчанию 1): ").strip()
        page = int(page) if page.isdigit() else 1
        
        data = {'page': page}
        response = self.make_request('GET', '/products', data)
        self.print_response(response)
    
    def get_product_detail(self):
        """Получение детальной информации о товаре"""
        print("\n6. Получение детальной информации о товаре")
        print("-" * 30)
        
        product_id = input("ID товара: ").strip()
        
        if not product_id:
            print("Ошибка: ID товара обязателен")
            return
        
        response = self.make_request('GET', f'/products/{product_id}')
        self.print_response(response)
    
    def create_product_requests_fallback(self, title, price, description, image_path):
        """Альтернативный способ создания товара"""
        try:
            with open(image_path, 'rb') as f:
                filename = os.path.basename(image_path)
                
                # ВАЖНО: Создаем НОВЫЙ сессию для этого запроса
                # чтобы избежать проблем с заголовками
                temp_session = requests.Session()
                
                files = {
                    'image': (filename, f)
                }
                
                data = {
                    'title': title,
                    'price': str(price),
                    'description': description
                }
                
                headers = {
                    'Authorization': f'Bearer {self.current_token}'
                }
                
                response = temp_session.post(
                    f'{API_URL}/products',
                    files=files,
                    data=data,
                    headers=headers
                )
                
                self.print_response(response)
                
        except Exception as e:
            print(f"❌ Ошибка fallback: {e}")

    def create_product_fixed(self):
        """Создание товара с исправленной загрузкой файла"""
        print("\n7. Создание нового товара")
        print("-" * 30)
        
        if not self.current_token:
            print("Ошибка: Сначала выполните вход или регистрацию")
            return
        
        title = input("Название товара: ").strip()
        price = input("Цена: ").strip()
        description = input("Описание (необязательно): ").strip()
        image_path = input("Путь к изображению: ").strip()
        
        if not all([title, price, image_path]):
            print("Ошибка: Все поля обязательны (ваш API требует изображение)")
            return
        
        try:
            price = int(price)
        except ValueError:
            print("Ошибка: Цена должна быть числом")
            return
        
        # Очистка пути
        image_path = image_path.strip('"\'')
        
        if not os.path.exists(image_path):
            print(f"❌ Файл не найден: {image_path}")
            return
        
        print(f"\nПодготовка запроса...")
        print(f"Название: {title}")
        print(f"Цена: {price}")
        print(f"Файл: {os.path.basename(image_path)}")
        
        try:
            # Используем subprocess для вызова curl (как в вашем рабочем примере)
            import subprocess
            
            # Формируем команду curl
            cmd = [
                'curl', '-X', 'POST',
                f'{API_URL}/products',
                '-H', f'Authorization: Bearer {self.current_token}',
                '-F', f'title={title}',
                '-F', f'price={price}',
                '-F', f'description={description}',
                '-F', f'image=@{image_path}',
                '--silent'
            ]
            
            print(f"\nВыполняем команду curl:")
            print(' '.join(cmd[:10]) + ' ...')
            
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
            
            # Пробуем альтернативный способ через requests
            print("\nПробуем альтернативный способ через requests...")
            self.create_product_requests_fallback(title, price, description, image_path)

    def create_product(self):
        """Создание нового товара"""
        print("\n7. Создание нового товара")
        print("-" * 30)
        
        if not self.current_token:
            print("Ошибка: Сначала выполните вход или регистрацию")
            return
        
        title = input("Название товара: ").strip()
        price = input("Цена: ").strip()
        description = input("Описание (необязательно): ").strip()
        image_path = input("Путь к изображению (необязательно): ").strip()
        
        if not title or not price:
            print("Ошибка: Название и цена обязательны")
            return
        
        try:
            price = int(price)
        except ValueError:
            print("Ошибка: Цена должна быть числом")
            return
        
        # Убираем кавычки если они есть
        if image_path:
            image_path = image_path.strip('"\'')
        
        # Проверяем файл
        if not image_path or not os.path.exists(image_path):
            print("❌ Файл не найден или не указан!")
            print("Ваш API требует изображение для создания товара.")
            return
        
        try:
            print(f"Загружаем файл: {os.path.basename(image_path)}")
            
            # Открываем файл
            with open(image_path, 'rb') as f:
                # Получаем имя файла
                filename = os.path.basename(image_path)
                
                # Создаем словарь для multipart/form-data
                # ВАЖНО: Используем кортеж (filename, file_object, content_type)
                files = {
                    'image': (filename, f, 'image/jpeg' if filename.lower().endswith('.jpg') else 
                            'image/png' if filename.lower().endswith('.png') else 
                            'image/gif' if filename.lower().endswith('.gif') else 
                            'application/octet-stream')
                }
                
                # Данные формы
                form_data = {
                    'title': title,
                    'price': str(price),
                    'description': description
                }
                
                print(f"Отправляем запрос с токеном: {self.current_token[:20]}...")
                
                # ВАЖНО: При использовании files=files, нужно передавать headers в post
                url = f"{API_URL}/products"
                headers = {
                    'Authorization': f'Bearer {self.current_token}'
                }
                
                # Делаем запрос
                response = self.session.post(
                    url,
                    data=form_data,
                    files=files,
                    headers=headers  # Заголовки передаются здесь
                )
                
                self.print_response(response)
                
        except FileNotFoundError:
            print(f"❌ Файл не найден: {image_path}")
        except Exception as e:
            print(f"❌ Ошибка: {e}")
    
    def create_product_with_curl(self):
        """Создание товара через curl (как в вашем рабочем примере)"""
        print("\n7. Создание товара (через curl)")
        print("-" * 30)
        
        if not self.current_token:
            print("Ошибка: Сначала выполните вход или регистрацию")
            return
        
        print("Введите данные товара:")
        title = input("Название товара: ").strip()
        price = input("Цена: ").strip()
        description = input("Описание: ").strip()
        
        print("\nУкажите путь к изображению:")
        print("(можно перетащить файл в окно терминала)")
        image_path = input("Путь: ").strip().strip('"\'')
        
        if not all([title, price, image_path]):
            print("❌ Все поля обязательны!")
            return
        
        if not os.path.exists(image_path):
            print(f"❌ Файл не найден: {image_path}")
            return
        
        try:
            # Формируем команду curl
            import subprocess
            import shlex
            
            # Экранируем специальные символы
            title_escaped = shlex.quote(title)
            description_escaped = shlex.quote(description)
            
            # Формируем команду
            curl_cmd = f'curl -X POST "{API_URL}/products" '
            curl_cmd += f'-H "Authorization: Bearer {self.current_token}" '
            curl_cmd += f'-F "title={title}" '
            curl_cmd += f'-F "price={price}" '
            curl_cmd += f'-F "description={description}" '
            curl_cmd += f'-F "image=@{image_path}"'
            
            print(f"\nВыполняем команду:\n{curl_cmd}")
            
            # Выполняем (для Windows используем shell=True)
            result = subprocess.run(
                curl_cmd,
                shell=True,
                capture_output=True,
                text=True
            )
            
            print(f"\nРезультат:")
            print(f"Статус: {result.returncode}")
            
            if result.stdout:
                try:
                    json_response = json.loads(result.stdout)
                    print(f"\nОтвет JSON:")
                    print(json.dumps(json_response, ensure_ascii=False, indent=2))
                except:
                    print(f"Ответ: {result.stdout}")
            
            if result.stderr:
                print(f"\nОшибка: {result.stderr}")
                
        except Exception as e:
            print(f"❌ Ошибка: {e}")

    def update_product_price(self):
        """Изменение цены товара"""
        print("\n8. Изменение цены товара")
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
        print("\n9. Подписка на товар")
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
        print("\n10. Отписка от товара")
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
        print("\n11. Снятие товара с продажи")
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
    
    def delete_burned_product(self):
        """Удаление прогоревшего товара"""
        print("\n12. Удаление прогоревшего товара")
        print("-" * 30)
        
        if not self.current_token:
            print("Ошибка: Сначала выполните вход или регистрацию")
            return
        
        product_id = input("ID товара: ").strip()
        
        if not product_id:
            print("Ошибка: ID товара обязателен")
            return
        
        response = self.make_request('DELETE', f'/products/{product_id}')
        self.print_response(response)
    
    def search_products(self):
        """Поиск товаров"""
        print("\n13. Поиск товаров")
        print("-" * 30)
        
        search_term = input("Поисковый запрос: ").strip()
        limit = input("Лимит результатов (по умолчанию 20): ").strip()
        min_score = input("Минимальный порог релевантности (0-1, по умолчанию 0.1): ").strip()
        
        if not search_term:
            print("Ошибка: Поисковый запрос обязателен")
            return
        
        params = {'q': search_term}
        if limit.isdigit():
            params['limit'] = int(limit)
        
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
        
        response = self.make_request('GET', '/account/subscriptions')
        self.print_response(response)
    
    def get_product_subscribers(self):
        """Получение подписчиков товара"""
        print("\n15. Получение подписчиков товара")
        print("-" * 30)
        
        product_id = input("ID товара: ").strip()
        
        if not product_id:
            print("Ошибка: ID товара обязателен")
            return
        
        response = self.make_request('GET', f'/products/{product_id}/subscribers')
        self.print_response(response)
    
    def logout(self):
        """Выход из системы"""
        print("\n14. Выход из системы")
        print("-" * 30)
        
        self.current_token = None
        self.current_user = None
        print("Успешно вышли из системы")
    
    def declare_bankruptcy(self):
        """Объявление банкротства"""
        print("\n15. Объявление банкротства")
        print("-" * 30)
        
        if not self.current_token:
            print("Ошибка: Сначала выполните вход или регистрацию")
            return
        
        print(f"Текущий пользователь: {self.current_user}")
        print("Проверяем возможность банкротства...")
        
        response = self.make_request('POST', '/account/bankruptcy')
        self.print_response(response)

    def get_toplist(self):
        """Получить список самых богатых игроков"""
        print("\n16. Получить список самых богатых игроков")
        print("-" * 30)

        page = input("Номер страницы (по умолчанию 1): ").strip()
        page = int(page) if page.isdigit() else 1
        
        data = {'page': page}
        response = self.make_request('GET', '/players/rating', data)
        self.print_response(response)

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
    
    def make_request(self, method, endpoint, data=None, headers=None, files=None):
        """Выполняет HTTP запрос с обработкой ошибок"""
        url = f"{API_URL}{endpoint}"
        
        # Добавляем токен авторизации, если есть
        request_headers = {}
        if headers:
            request_headers.update(headers)
        
        if self.current_token:
            request_headers['Authorization'] = f'Bearer {self.current_token}'
            if self.debug:
                print(f"[DEBUG] Adding Authorization header with token: {self.current_token[:20]}...")
        
        if self.debug:
            print(f"[DEBUG] Making {method} request to {url}")
            print(f"[DEBUG] Headers: {request_headers}")
            print(f"[DEBUG] Has files: {files is not None}")
            if data and not files:
                print(f"[DEBUG] JSON Data: {data}")
            elif data and files:
                print(f"[DEBUG] Form Data: {data}")
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, params=data, headers=request_headers)
            elif method.upper() == 'POST':
                if files:
                    # Для multipart/form-data
                    # ВАЖНО: НЕ передаем headers здесь, они будут установлены автоматически
                    # с правильным Content-Type с boundary
                    response = self.session.post(url, data=data, files=files)
                    # Добавляем Authorization header после создания запроса
                    if self.current_token:
                        response.request.headers['Authorization'] = f'Bearer {self.current_token}'
                else:
                    response = self.session.post(url, json=data, headers=request_headers)
            elif method.upper() == 'PUT':
                response = self.session.put(url, json=data, headers=request_headers)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url, json=data, headers=request_headers)
            else:
                raise ValueError(f"Неподдерживаемый метод: {method}")
            
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
        print("\n17. Прямой запрос (для отладки)")
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
        
        # Показываем сырые байты для отладки
        if response:
            print("\nСырые байты ответа:")
            print(response.content[:500])
            print(f"\nКодировка ответа: {response.encoding}")
            print(f"Заголовки ответа: {dict(response.headers)}")
    
    def fix_encoding_problem(self):
        """Попытка исправить проблему с кодировкой вручную"""
        print("\n18. Исправление проблемы кодировки")
        print("-" * 30)
        
        # Тестовый запрос для диагностики
        response = self.make_request('GET', '/health')
        
        if response:
            print("Диагностика кодировки:")
            print(f"Заголовки: {dict(response.headers)}")
            print(f"Заявленная кодировка: {response.encoding}")
            print(f"Длина контента: {len(response.content)} байт")
            
            # Пробуем разные кодировки
            encodings = ['utf-8', 'cp1251', 'iso-8859-1', 'koi8-r', 'cp866', 'utf-16']
            
            for enc in encodings:
                try:
                    decoded = response.content.decode(enc)
                    if 'healthy' in decoded or 'status' in decoded:
                        print(f"\n✓ Найдена правильная кодировка: {enc}")
                        print(f"Пример текста: {decoded[:100]}")
                        break
                except:
                    print(f"✗ Не удалось декодировать как {enc}")
    
    def main_menu(self):
        """Главное меню"""
        while True:
            self.clear_screen()
            print("=" * 60)
            print("API ТЕСТЕР ДЛЯ МАРКЕТПЛЕЙСА")
            print("=" * 60)
            
            self.show_status()
            
            print("\nВыберите действие:")
            print("=" * 60)
            print(" 1. Проверка здоровья сервера")
            print(" 2. Регистрация")
            print(" 3. Вход")
            print(" 4. Получить профиль")
            print(" 5. Получить список товаров")
            print(" 6. Получить детали товара")
            print(" 7. Создать товар")
            print(" 8. Изменить цену товара")
            print(" 9. Подписаться на товар")
            print("10. Отписаться от товара")
            print("11. Снять товар с продажи")
            # # print("12. Удалить прогоревший товар")
            # print("13. Поиск товаров")
            # print("14. Мои подписки")
            # # print("15. Подписчики товара")
            # print("16. Выйти из системы (Разлогиниться)")
            # # print("17. Прямой запрос (отладка)")
            # # print("18. Диагностика кодировки")
            # print(" 0. Выход из программы")
            # # print("12. Удалить прогоревший товар")
            print("12. Поиск товаров")
            print("13. Мои подписки")
            print("14. Выйти из системы (Разлогиниться)")
            print("15. Объявить банкротство")
            print("16. Самые богатые игроки")
            print(" 0. Выход из программы")
            print("=" * 60)
            
            choice = input("\nВаш выбор (0-18): ").strip()
            
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
                self.get_profile()
                self.wait_for_input()
            elif choice == '5':
                self.get_products()
                self.wait_for_input()
            elif choice == '6':
                self.get_product_detail()
                self.wait_for_input()
            elif choice == '7':
                self.create_product_with_curl()
                self.wait_for_input()
            elif choice == '8':
                self.update_product_price()
                self.wait_for_input()
            elif choice == '9':
                self.subscribe_to_product()
                self.wait_for_input()
            elif choice == '10':
                self.unsubscribe_from_product()
                self.wait_for_input()
            elif choice == '11':
                self.remove_product()
                self.wait_for_input()
            elif choice == '12':
                self.search_products()
                self.wait_for_input()
            elif choice == '13':
                self.get_user_subscriptions()
                self.wait_for_input()
            elif choice == '14':
                self.logout()
                self.wait_for_input()
            elif choice == '15':
                self.declare_bankruptcy()
                self.wait_for_input()
            elif choice == '16':
                self.get_toplist()
                self.wait_for_input()
            else:
                print("\nНеверный выбор. Попробуйте снова.")
                self.wait_for_input()

def main():
    """Точка входа в программу"""
    print("Запуск API тестера...")
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
                print("✓ Сервер работает корректно")
            else:
                print("⚠ Сервер отвечает, но ответ не соответствует ожидаемому формату")
        else:
            print("✗ Сервер не ответил")
    except Exception as e:
        print(f"✗ Ошибка подключения: {e}")
    
    tester.wait_for_input("Нажмите Enter для продолжения в главное меню...")
    tester.main_menu()

if __name__ == "__main__":
    main()
