import requests
import json
from typing import Optional, Dict, List
from datetime import datetime, timedelta


class CurrencyConverter:
    
    def __init__(self, api_url: str = "https://api.exchangerate-api.com/v4/latest"):
        self.api_url = api_url
        self.cache: Dict[str, Dict] = {}
        self.cache_timestamps: Dict[str, datetime] = {}
        self.cache_duration = timedelta(minutes=5)  # Кэш на 5 минут
    
    def get_exchange_rates(self, base_currency: str = "USD", force_update: bool = False) -> Optional[Dict]:
        try:
            if not force_update and base_currency in self.cache:
                if base_currency in self.cache_timestamps:
                    cache_age = datetime.now() - self.cache_timestamps[base_currency]
                    if cache_age < self.cache_duration:
                        return self.cache[base_currency]

            url = f"{self.api_url}/{base_currency}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()

            if data and "rates" in data and "RUB" in data["rates"]:
                rub_data = self._get_rub_rate_from_cbr()
                if rub_data:
                    if base_currency.upper() == "USD" and "USD" in rub_data:
                        data["rates"]["RUB"] = rub_data["USD"]
                    elif base_currency.upper() == "EUR" and "EUR" in rub_data:
                        data["rates"]["RUB"] = rub_data["EUR"]

            self.cache[base_currency] = data
            self.cache_timestamps[base_currency] = datetime.now()
            
            return data
            
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при получении данных: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"Ошибка при обработке JSON: {e}")
            return None
    
    def _get_rub_rate_from_cbr(self) -> Optional[Dict[str, float]]:
        try:
            url = "https://www.cbr-xml-daily.ru/daily_json.js"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if "Valute" not in data:
                return None
            
            rates = {}
            valute = data["Valute"]

            if "USD" in valute:
                rates["USD"] = valute["USD"]["Value"] / valute["USD"]["Nominal"]

            if "EUR" in valute:
                rates["EUR"] = valute["EUR"]["Value"] / valute["EUR"]["Nominal"]
            
            return rates
            
        except Exception:
            return None
    
    def clear_cache(self):
        self.cache.clear()
        self.cache_timestamps.clear()
    
    def convert(self, amount: float, from_currency: str, to_currency: str, force_update: bool = False) -> Optional[float]:

        if from_currency.upper() == to_currency.upper():
            return amount

        if "RUB" in [from_currency.upper(), to_currency.upper()]:
            force_update = True

        rates_data = self.get_exchange_rates(from_currency.upper(), force_update=force_update)
        
        if not rates_data or 'rates' not in rates_data:
            print(f"Не удалось получить курсы валют для {from_currency}")
            return None
        
        rates = rates_data['rates']

        if to_currency.upper() not in rates:
            print(f"Валюта {to_currency} не найдена в списке доступных валют")
            return None

        exchange_rate = rates[to_currency.upper()]
        converted_amount = amount * exchange_rate
        
        return converted_amount
    
    def get_available_currencies(self, base_currency: str = "USD") -> List[str]:
        rates_data = self.get_exchange_rates(base_currency.upper())
        
        if not rates_data or 'rates' not in rates_data:
            return []
        
        currencies = list(rates_data['rates'].keys())
        currencies.append(base_currency.upper())  # Добавляем базовую валюту
        return sorted(currencies)
    
    def get_rate(self, from_currency: str, to_currency: str, force_update: bool = False) -> Optional[float]:

        if from_currency.upper() == to_currency.upper():
            return 1.0

        if "RUB" in [from_currency.upper(), to_currency.upper()]:
            force_update = True
        
        rates_data = self.get_exchange_rates(from_currency.upper(), force_update=force_update)
        
        if not rates_data or 'rates' not in rates_data:
            return None
        
        rates = rates_data['rates']
        
        if to_currency.upper() not in rates:
            return None
        
        return rates[to_currency.upper()]


def print_currency_list(converter: CurrencyConverter):
    popular_currencies = {
        'USD': 'Доллар США',
        'EUR': 'Евро',
        'GBP': 'Фунт стерлингов',
        'JPY': 'Японская йена',
        'CNY': 'Китайский юань',
        'RUB': 'Российский рубль',
        'INR': 'Индийская рупия',
        'BRL': 'Бразильский реал',
        'CAD': 'Канадский доллар',
        'AUD': 'Австралийский доллар',
        'CHF': 'Швейцарский франк',
        'KRW': 'Южнокорейская вона',
        'MXN': 'Мексиканское песо',
        'SGD': 'Сингапурский доллар',
        'HKD': 'Гонконгский доллар',
    }
    
    print("\nПопулярные валюты:")
    print("-" * 50)
    for code, name in popular_currencies.items():
        print(f"{code:5} - {name}")


def main():
    converter = CurrencyConverter()
    
    print("=" * 60)
    print("          КОНВЕРТЕР ВАЛЮТ")
    print("=" * 60)
    print("\nИспользуется открытый API для получения актуальных курсов")
    
    while True:
        print("\n" + "-" * 60)
        print("Выберите действие:")
        print("1. Конвертировать валюту")
        print("2. Узнать курс обмена")
        print("3. Показать список популярных валют")
        print("4. Обновить курсы валют (очистить кэш)")
        print("5. Выход")
        print("-" * 60)
        
        choice = input("\nВаш выбор (1-5): ").strip()
        
        if choice == "1":
            try:
                amount = float(input("\nВведите сумму для конвертации: "))
                from_curr = input("Введите код исходной валюты (например, USD): ").strip().upper()
                to_curr = input("Введите код целевой валюты (например, EUR): ").strip().upper()

                if "RUB" in [from_curr, to_curr]:
                    print("Обновление актуальных курсов...")
                
                print(f"\nКонвертация {amount} {from_curr} в {to_curr}...")
                result = converter.convert(amount, from_curr, to_curr)
                
                if result is not None:
                    print(f"\nРезультат: {amount:,.2f} {from_curr} = {result:,.2f} {to_curr}")
                    rate = converter.get_rate(from_curr, to_curr)
                    if rate:
                        print(f"  Курс: 1 {from_curr} = {rate:.4f} {to_curr}")
                        if "RUB" in [from_curr, to_curr]:
                            print("  (Используются актуальные данные от ЦБ РФ)")
                else:
                    print("Ошибка при конвертации. Проверьте коды валют.")
                    
            except ValueError:
                print("Ошибка: введите корректное число")
            except KeyboardInterrupt:
                print("\n\nОперация отменена")
        
        elif choice == "2":
            try:
                from_curr = input("\nВведите код исходной валюты (например, USD): ").strip().upper()
                to_curr = input("Введите код целевой валюты (например, EUR): ").strip().upper()

                if "RUB" in [from_curr, to_curr]:
                    print("Обновление актуальных курсов...")
                
                rate = converter.get_rate(from_curr, to_curr)
                
                if rate is not None:
                    print(f"\n✓ Курс обмена: 1 {from_curr} = {rate:.4f} {to_curr}")
                    print(f"  Обратный курс: 1 {to_curr} = {1/rate:.4f} {from_curr}")
                    if "RUB" in [from_curr, to_curr]:
                        print("  (Используются актуальные данные от ЦБ РФ)")
                else:
                    print("Ошибка при получении курса. Проверьте коды валют.")
                    
            except KeyboardInterrupt:
                print("\n\nОперация отменена")
        
        elif choice == "4":
            converter.clear_cache()
            print("\n✓ Кэш очищен. При следующем запросе будут загружены актуальные курсы.")
        
        elif choice == "3":
            print_currency_list(converter)
        
        elif choice == "5":
            print("\nДо свидания!")
            break
        
        else:
            print("Неверный выбор. Пожалуйста, выберите от 1 до 5.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nПрограмма завершена пользователем.")
    except Exception as e:
        print(f"\nПроизошла ошибка: {e}")

