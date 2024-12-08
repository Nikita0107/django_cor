from mi_django.models import Doc, Cart, Price, UsersToDocs

def run():
    """
    Удаляет все объекты из таблиц Doc, Cart, Price и UsersToDocs после подтверждения.
    """
    confirm = input("Вы уверены, что хотите удалить все объекты из всех таблиц? (yes/no): ")
    if confirm.lower() == "yes":
        # Удаляем данные из каждой модели
        Doc.objects.all().delete()
        Cart.objects.all().delete()
        Price.objects.all().delete()
        UsersToDocs.objects.all().delete()

        print("Все объекты из таблиц Doc, Cart, Price и UsersToDocs были успешно удалены.")
    else:
        print("Операция удаления отменена.")


# python manage.py shell

'''from scripts.clear_table import run
run()'''