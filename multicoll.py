import json
import asyncio
from web3 import AsyncWeb3
from web3.providers.async_rpc import AsyncHTTPProvider


w3_async = AsyncWeb3(AsyncHTTPProvider('https://rpc.ankr.com/arbitrum')) # УКАЖИТЕ РПС НУЖНОЙ СЕТИ

viev = 1 # Вид ответа; при варианте 1
             # Балансы для USDC:
                # 0x21906Db0Bec3cD9d4b3177ABD4bE5b7Eb8945e34;0.000
                # 0x3038b24c79724dec422312879c9DfB3d3CaCd26B;0.000
                # 0xD3eC1c7Ea0a0798184EDad45Bb625FF37606d89E;0.000
         # Вид ответа; при варианте 2
                # Балансы 0x21906Db0Bec3cD9d4b3177ABD4bE5b7Eb8945e34
                # USDC=0.000
                # USDT=0.000
                # WETH=0.000


rasdelitel = True # True если нужно добавить разделитель ; для импорта в таблицу и разделения

tokens = ["USDT_ADDRESS","USDC_ADDRESS","YOUR_CONTRACT"] # УКАЖИТЕ КОНТРАКТЫ НУЖНЫХ МОНЕТ ЧЕРЕЗ ЗАПЯТУЮ

with open('abis/abi.json') as file:
    ERC20_ABI = json.load(file)

with open('abis/multicoll.json') as file:
    Multicol_json = json.load(file)



MULTICALL_ADDRESS = "0xcA11bde05977b3631167028862bE2a173976CA11"  # УКАЖИТЕ КОНТРАКТ МУЛЬТИКОЛА




balance_calls = []

decoded_values = []

with open("wallet.txt", 'r') as f:
    wallet = [line.strip() for line in f.readlines()]



async def balances_from_multicall(): # ЗАПРОС НА ИНФУ О БАЛАНСАХ


    multicall_contract: AsyncContract = w3_async.eth.contract(
        address=w3_async.to_checksum_address(MULTICALL_ADDRESS),
        abi=Multicol_json
    )


    for token_address in tokens:
        for wallets in wallet:
            token_contract: AsyncContract = w3_async.eth.contract(
                address=w3_async.to_checksum_address(token_address),
                abi=ERC20_ABI
            )

            balance_call = token_contract.encodeABI(
                fn_name='balanceOf',
                args=([
                    wallets
                ])
            )

            balance_calls.append([
                w3_async.to_checksum_address(token_address),
                False,
                balance_call
            ])

    balance_data = await multicall_contract.functions.aggregate3(balance_calls).call()


    for success, byte_string in balance_data: # ДЕКОДИРОВАНИЕ РЕЗУЛЬТАТА ИЗ БАЙТ
        if success:
            # Decode the byte string to an integer
            value = int.from_bytes(byte_string, byteorder="big")
            decoded_values.append(value)

        else:
            decoded_values.append(None)



async def result():

    await balances_from_multicall()

    wallet_balances = {address: {token: 0 for token in tokens} for address in wallet}

    if viev == 2:
        # Распределяем значения по кошелькам и токенам
        index = 0
        for address in wallet:
            for token in tokens:
                if index < len(decoded_values):
                    wallet_balances[address][token] = decoded_values[index]
                    index += 1


        for address in wallet:
            print(f"Балансы {address}")
            for token in tokens:
                contract = w3_async.eth.contract(
                    address=w3_async.to_checksum_address(token),
                    abi=ERC20_ABI
                )
                print(f"{await contract.functions.symbol().call()}={wallet_balances[address][token]/10**6:.3f}")

    if viev == 1:
        # Распределяем значения по кошелькам и токенам
        index = 0
        for address in wallet:
            for token in tokens:
                if index < len(decoded_values):
                    wallet_balances[address][token] = decoded_values[index]
                    index += 1

        # Вывод в требуемом формате
        for token in tokens:
            contract = w3_async.eth.contract(
                address=w3_async.to_checksum_address(token),
                abi=ERC20_ABI
            )
            print(f"Балансы для {await contract.functions.symbol().call()}:")
            for address in wallet:
                if rasdelitel == False:
                    print(f"{address} = {wallet_balances[address][token] / 10 ** 6:.3f}")
                if rasdelitel == True:
                    print(f"{address};{wallet_balances[address][token] / 10 ** 6:.3f}")
            print()  # Разделитель между токенами


asyncio.run(result())

