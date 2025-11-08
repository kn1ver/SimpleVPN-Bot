from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

start = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='Установить VPN', callback_data='install_vpn')],
        [InlineKeyboardButton(text='Оплатить VPN', callback_data='pay_vpn')],
        [InlineKeyboardButton(text='Поддержка', callback_data='help')],
        [InlineKeyboardButton(text='Профиль', callback_data='profile')]
    ],  input_field_placeholder='Выберите пункт',)

to_main = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='Назад', callback_data='return_to_main')]
    ])

to_platforms = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='Назад', callback_data='return_to_platforms')]
    ])

pc = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='Получить установщик', callback_data='install_pc_get_installer')],
        [InlineKeyboardButton(text='Назад', callback_data='return_to_platforms')]
    ])

buy_vpn = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='Купить/Продлить VPN', callback_data='buy_vpn')],
        [InlineKeyboardButton(text='Назад', callback_data='return_to_main')]
    ])

pay_vpn = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='Купить/Оплатить VPN', callback_data='pay_vpn')],
        [InlineKeyboardButton(text='Назад', callback_data='return_to_main')]
    ])

platforms = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='Компьютер', callback_data='install_pc')],
        [InlineKeyboardButton(text='Android', callback_data='install_android')],
        [InlineKeyboardButton(text='IOS', callback_data='install_ios')],
        [InlineKeyboardButton(text='Назад', callback_data='return_to_main')]
    ])

def approve_payment(client_id: str) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='Подтвердить', callback_data=f'payment_approve_{client_id}')],
        [InlineKeyboardButton(text='Отклонить', callback_data=f'payment_deny_{client_id}')]
    ])
    return keyboard
