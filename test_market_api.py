#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import os
import subprocess
import sys

# Конфигурация
BASE_URL = "http://127.0.0.1:5000" if len(sys.argv) < 2 else f"http://{sys.argv[1]}:5000"
API_URL = f"{BASE_URL}/api"

class APITester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'APITester/4.0'
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
        method = getattr(response, '_method', 'GET')
        
        # Получаем отправленные данные
        request_data = getattr(response, '_sent_data', None)
        
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
        
        if response.status_code != 200 and response.status_code != 201:
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
                if header.lower() not in ['date', 'server']:
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
    
    def make_request(self, method, endpoint, data=None, headers=None, files=None, params=None):
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
        
        if self.debug:
            print(f"[DEBUG] Making {method} request to {url}")
            print(f"[DEBUG] Headers: {request_headers}")
            if data and not files:
                print(f"[DEBUG] Data to send: {data}")
            if params:
                print(f"[DEBUG] Params: {params}")
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, params=params or data, headers=request_headers)
                response._sent_data = params or data
                response._method = 'GET'
                
            elif method.upper() == 'POST':
                if files:
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
                response._sent_data = None
                response._method = 'DELETE'
                
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
    
    # ========== НОВЫЕ МЕТОДЫ ДЛЯ API v4.0 ==========
    
    def test_health_check(self):
        """Тест health check эндпоинта"""
        print("\n1. Проверка здоровья сервера")
        print("-" * 30)
        response = self.make_request('GET', '/health')
        return self.print_response(response)
    
    def register(self):
        """Регистрация нового пользователя (с бонусом 200 AC)"""
        print("\n2. Регистрация нового пользователя")
        print("-" * 30)
        print("ℹ️  При регистрации начисляется бонус 200 AC")
        
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
                balance = result['user'].get('balance')
                print(f"\n✓ Автоматически авторизован как: {self.current_user}")
                print(f"✓ Баланс: {balance} AC (включая бонус за регистрацию)")
                print(f"✓ Токен получен: {self.current_token[:20]}...")
            else:
                print(f"\n✗ Не удалось получить токен из ответа")
    
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
                print(f"✓ Токен получен: {self.current_token[:20]}...")
            else:
                print(f"\n✗ Не удалось получить токен из ответа")
    
    def refresh_token(self):
        """Обновление токена"""
        print("\n4. Обновление токена")
        print("-" * 30)
        
        if not self.current_token:
            print("Ошибка: Сначала выполните вход или регистрацию")
            return
        
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
                print(f"\n✓ Токен обновлен: {self.current_token[:20]}...")
    
    def get_profile(self):
        """Получение профиля текущего пользователя (с товарами на продаже и купленными)"""
        print("\n5. Получение профиля пользователя")
        print("-" * 30)
        
        if not self.current_token:
            print("Ошибка: Сначала выполните вход или регистрацию")
            return
        
        response = self.make_request('GET', '/auth/profile')
        self.print_response(response)
    
    def get_products(self):
        """Получение списка товаров (только непроданные, с водяным знаком)"""
        print("\n6. Получение списка товаров")
        print("-" * 30)
        print("ℹ️  Отображаются только непроданные товары с водяным знаком")
        
        page = input("Номер страницы (по умолчанию 1): ").strip()
        page = int(page) if page.isdigit() else 1
        
        params = {'page': page}
        
        response = self.make_request('GET', '/products', params=params)
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
    
    def create_product(self):
        """Создание товара (без списания средств)"""
        print("\n8. Создание товара")
        print("-" * 30)
        
        if not self.current_token:
            print("Ошибка: Сначала выполните вход или регистрацию")
            return
        
        print("Введите данные товара:")
        title = input("Название товара (3-100 символов): ").strip()
        price = input(f"Цена (10-10000 AC): ").strip()
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
            cmd = [
                'curl', '-X', 'POST',
                f'{API_URL}/products',
                '-H', f'Authorization: Bearer {self.current_token}',
                '-F', f'title={title}',
                '-F', f'price={price}',
                '--silent'
            ]
            
            if description:
                cmd.extend(['-F', f'description={description}'])
            
            cmd.extend(['-F', f'image=@{image_path}'])
            
            print(f"\nВыполняем команду curl...")
            
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
            
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
    
    def buy_product(self):
        """Покупка товара"""
        print("\n9. Покупка товара")
        print("-" * 30)
        
        if not self.current_token:
            print("Ошибка: Сначала выполните вход или регистрацию")
            return
        
        product_id = input("ID товара: ").strip()
        
        if not product_id:
            print("Ошибка: ID товара обязателен")
            return
        
        print("\nℹ️  При покупке списывается полная стоимость товара")
        print("ℹ️  Комиссия 5% сгорает, остальное получает продавец")
        print("ℹ️  После покупки товар переходит в вашу коллекцию")
        
        confirm = input("\nПодтвердить покупку? (y/n): ").strip().lower()
        
        if confirm != 'y':
            print("Покупка отменена")
            return
        
        response = self.make_request('POST', f'/products/{product_id}/buy')
        self.print_response(response)
    
    def remove_product(self):
        """Удаление товара (только если не продан)"""
        print("\n10. Удаление товара")
        print("-" * 30)
        
        if not self.current_token:
            print("Ошибка: Сначала выполните вход или регистрацию")
            return
        
        product_id = input("ID товара: ").strip()
        
        if not product_id:
            print("Ошибка: ID товара обязателен")
            return
        
        print("\n⚠️  Внимание: Товар будет полностью удален из системы")
        print("⚠️  Это действие нельзя отменить")
        print("⚠️  Удалить можно только непроданный товар")
        
        confirm = input("\nПодтвердить удаление? (y/n): ").strip().lower()
        
        if confirm != 'y':
            print("Удаление отменено")
            return
        
        response = self.make_request('POST', f'/products/{product_id}/remove')
        self.print_response(response)
    
    def search_products(self):
        """Поиск товаров"""
        print("\n11. Поиск товаров")
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
        
        response = self.make_request('GET', '/products/search', params=params)
        self.print_response(response)
    
    def get_purchases(self):
        """История покупок"""
        print("\n12. История покупок")
        print("-" * 30)
        
        if not self.current_token:
            print("Ошибка: Сначала выполните вход или регистрацию")
            return
        
        page = input("Номер страницы (по умолчанию 1): ").strip()
        page = int(page) if page.isdigit() else 1
        
        per_page = input("Количество на странице (по умолчанию 20): ").strip()
        per_page = int(per_page) if per_page.isdigit() else 20
        
        params = {
            'page': page,
            'per_page': per_page
        }
        
        response = self.make_request('GET', '/account/purchases', params=params)
        self.print_response(response)
    
    def get_sales(self):
        """История продаж"""
        print("\n13. История продаж")
        print("-" * 30)
        
        if not self.current_token:
            print("Ошибка: Сначала выполните вход или регистрацию")
            return
        
        page = input("Номер страницы (по умолчанию 1): ").strip()
        page = int(page) if page.isdigit() else 1
        
        per_page = input("Количество на странице (по умолчанию 20): ").strip()
        per_page = int(per_page) if per_page.isdigit() else 20
        
        params = {
            'page': page,
            'per_page': per_page
        }
        
        response = self.make_request('GET', '/account/sales', params=params)
        self.print_response(response)
    
    def get_stats(self):
        """Статистика профиля (график баланса)"""
        print("\n14. Статистика профиля")
        print("-" * 30)
        
        if not self.current_token:
            print("Ошибка: Сначала выполните вход или регистрацию")
            return
        
        response = self.make_request('GET', '/account/stats')
        self.print_response(response)
    
    def claim_daily_bonus(self):
        """Получение ежедневного бонуса"""
        print("\n15. Получение ежедневного бонуса")
        print("-" * 30)
        
        if not self.current_token:
            print("Ошибка: Сначала выполните вход или регистрацию")
            return
        
        print("ℹ️  Условия получения бонуса:")
        print("   - Можно получать 1 раз в день")
        print("   - Баланс должен быть меньше 500 AC")
        print(f"   - Сумма бонуса: 50 AC")
        
        confirm = input("\nПолучить бонус? (y/n): ").strip().lower()
        
        if confirm != 'y':
            print("Отменено")
            return
        
        response = self.make_request('POST', '/account/daily-bonus')
        self.print_response(response)
    
    def declare_bankruptcy(self):
        """Объявление банкротства"""
        print("\n16. Объявление банкротства")
        print("-" * 30)
        
        if not self.current_token:
            print("Ошибка: Сначала выполните вход или регистрацию")
            return
        
        print(f"Текущий пользователь: {self.current_user}")
        print("ℹ️  Условия банкротства:")
        print("   - Можно объявлять 1 раз в день")
        print("   - Баланс должен быть меньше 100 AC")
        print("   - Нет активных товаров на продаже")
        print("   - После банкротства баланс становится 100 AC")
        
        confirm = input("\nВы уверены? (y/n): ").strip().lower()
        
        if confirm != 'y':
            print("Отменено")
            return
        
        response = self.make_request('POST', '/account/bankruptcy')
        self.print_response(response)
    
    def get_rating(self):
        """Самые богатые игроки"""
        print("\n17. Самые богатые игроки")
        print("-" * 30)

        page = input("Номер страницы (по умолчанию 1): ").strip()
        page = int(page) if page.isdigit() else 1
        
        per_page = input("Количество игроков на странице (1-100, по умолчанию 20): ").strip()
        per_page = int(per_page) if per_page.isdigit() else 20
        
        params = {
            'page': page,
            'per_page': min(max(per_page, 1), 100)
        }
        
        response = self.make_request('GET', '/players/rating', params=params)
        self.print_response(response)
    
    def get_original_image(self):
        """Получение оригинального изображения (только для владельца)"""
        print("\n18. Получение оригинального изображения")
        print("-" * 30)
        print("ℹ️  Доступно только владельцу товара (создателю или покупателю)")
        
        if not self.current_token:
            print("Ошибка: Сначала выполните вход или регистрацию")
            return
        
        file_id = input("ID файла изображения: ").strip()
        
        if not file_id:
            print("Ошибка: ID файла обязателен")
            return
        
        url = f"{API_URL}/images/original/{file_id}"
        print(f"URL: {url}")
        
        try:
            headers = {'Authorization': f'Bearer {self.current_token}'}
            response = requests.get(url, headers=headers, stream=True)
            
            if response.status_code == 200:
                print(f"✓ Изображение найдено, размер: {len(response.content)} байт")
                print(f"✓ Content-Type: {response.headers.get('content-type')}")
                
                save = input("Сохранить изображение? (y/n): ").strip().lower()
                if save == 'y':
                    filename = input("Имя файла для сохранения (по умолчанию original.jpg): ").strip()
                    if not filename:
                        filename = 'original.jpg'
                    
                    with open(filename, 'wb') as f:
                        f.write(response.content)
                    print(f"✓ Изображение сохранено как {filename}")
            elif response.status_code == 404:
                print("✗ Изображение не найдено или у вас нет прав доступа")
            else:
                print(f"✗ Ошибка: {response.status_code}")
        except Exception as e:
            print(f"✗ Ошибка при загрузке изображения: {e}")
    
    def get_watermarked_image(self):
        """Получение изображения с водяным знаком (доступно всем)"""
        print("\n19. Получение изображения с водяным знаком")
        print("-" * 30)
        print("ℹ️  Доступно всем, но только для непроданных товаров")
        
        file_id = input("ID файла изображения: ").strip()
        
        if not file_id:
            print("Ошибка: ID файла обязателен")
            return
        
        url = f"{API_URL}/images/watermarked/{file_id}"
        print(f"URL: {url}")
        
        try:
            response = requests.get(url, stream=True)
            
            if response.status_code == 200:
                print(f"✓ Изображение найдено, размер: {len(response.content)} байт")
                print(f"✓ Content-Type: {response.headers.get('content-type')}")
                
                save = input("Сохранить изображение? (y/n): ").strip().lower()
                if save == 'y':
                    filename = input("Имя файла для сохранения (по умолчанию watermarked.jpg): ").strip()
                    if not filename:
                        filename = 'watermarked.jpg'
                    
                    with open(filename, 'wb') as f:
                        f.write(response.content)
                    print(f"✓ Изображение сохранено как {filename}")
            elif response.status_code == 404:
                print("✗ Изображение не найдено или товар уже продан")
            else:
                print(f"✗ Ошибка: {response.status_code}")
        except Exception as e:
            print(f"✗ Ошибка при загрузке изображения: {e}")
    
    def logout(self):
        """Выход из системы"""
        print("\n20. Выход из системы")
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
        print(f"API версия: 4.0 (Маркетплейс)")
    
    def test_raw_request(self):
        """Прямой запрос для отладки"""
        print("\n21. Прямой запрос (для отладки)")
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
            print("API ТЕСТЕР ДЛЯ МАРКЕТПЛЕЙСА v4.0")
            print("=" * 60)
            
            self.show_status()
            
            print("\nВыберите действие:")
            print("=" * 60)
            print(" 1. Проверка здоровья сервера")
            print(" 2. Регистрация (+200 AC бонус)")
            print(" 3. Вход")
            print(" 4. Обновить токен")
            print(" 5. Профиль (товары на продаже + купленные)")
            print(" 6. Список товаров (с водяным знаком)")
            print(" 7. Детали товара")
            print(" 8. Создать товар")
            print(" 9. Купить товар")
            print("10. Удалить товар (только непроданный)")
            print("11. Поиск товаров")
            print("12. История покупок")
            print("13. История продаж")
            print("14. Статистика профиля (график баланса)")
            print("15. Получить ежедневный бонус (+50 AC)")
            print("16. Объявить банкротство")
            print("17. Рейтинг игроков")
            print("18. Оригинальное изображение (только владельцу)")
            print("19. Изображение с водяным знаком")
            print("20. Выйти из системы")
            print("21. Прямой запрос (отладка)")
            print(" 0. Выход из программы")
            print("=" * 60)
            
            choice = input("\nВаш выбор (0-21): ").strip()
            
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
                self.create_product()
                self.wait_for_input()
            elif choice == '9':
                self.buy_product()
                self.wait_for_input()
            elif choice == '10':
                self.remove_product()
                self.wait_for_input()
            elif choice == '11':
                self.search_products()
                self.wait_for_input()
            elif choice == '12':
                self.get_purchases()
                self.wait_for_input()
            elif choice == '13':
                self.get_sales()
                self.wait_for_input()
            elif choice == '14':
                self.get_stats()
                self.wait_for_input()
            elif choice == '15':
                self.claim_daily_bonus()
                self.wait_for_input()
            elif choice == '16':
                self.declare_bankruptcy()
                self.wait_for_input()
            elif choice == '17':
                self.get_rating()
                self.wait_for_input()
            elif choice == '18':
                self.get_original_image()
                self.wait_for_input()
            elif choice == '19':
                self.get_watermarked_image()
                self.wait_for_input()
            elif choice == '20':
                self.logout()
                self.wait_for_input()
            elif choice == '21':
                self.test_raw_request()
                self.wait_for_input()
            else:
                print("\nНеверный выбор. Попробуйте снова.")
                self.wait_for_input()

def main():
    """Точка входа в программу"""
    print("Запуск API тестера для Market API v4.0...")
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
        else:
            print("✗ Сервер не ответил")
    except Exception as e:
        print(f"✗ Ошибка подключения: {e}")
    
    tester.wait_for_input("Нажмите Enter для продолжения в главное меню...")
    tester.main_menu()

if __name__ == "__main__":
    main()
