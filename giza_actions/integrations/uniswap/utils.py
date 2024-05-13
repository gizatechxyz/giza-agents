import json
import math

from ape import Contract

from giza_actions.integrations.uniswap.constants import (
    MAX_TICK,
    MIN_TICK,
    Q96,
    TICKS_Q,
    _tick_spacing,
)


def load_contract(address):
    return Contract(address)


def price_to_tick(price):
    sqrtPriceX96 = int(price * 2**96)
    tick = math.floor(math.log((sqrtPriceX96 / Q96) ** 2) / math.log(TICKS_Q))
    return tick


def price_to_sqrtp(p):
    return int(math.sqrt(p) * Q96)


def tick_to_price(tick, decimals0, decimals1, invert=False):
    if invert:
        return 1 / (TICKS_Q**tick / 10 ** (decimals1 - decimals0))
    else:
        return TICKS_Q**tick / 10 ** (decimals1 - decimals0)


def get_min_tick(fee):
    min_tick_spacing = _tick_spacing[fee]
    return -(MIN_TICK // -min_tick_spacing) * min_tick_spacing


def get_max_tick(fee):
    max_tick_spacing = _tick_spacing[fee]
    return (MAX_TICK // max_tick_spacing) * max_tick_spacing


def default_tick_range(fee):
    min_tick = get_min_tick(fee)
    max_tick = get_max_tick(fee)
    return min_tick, max_tick


# https://uniswapv3book.com/milestone_1/calculating-liquidity.html
def calc_amount0(liq, pa, pb):
    if pa > pb:
        pa, pb = pb, pa
    return int(liq * Q96 * (pb - pa) / pa / pb)


def calc_amount1(liq, pa, pb):
    if pa > pb:
        pa, pb = pb, pa
    return int(liq * (pb - pa) / Q96)


def liquidity0(amount, pa, pb):
    if pa > pb:
        pa, pb = pb, pa
    return (amount * (pa * pb) / Q96) / (pb - pa)


def liquidity1(amount, pa, pb):
    if pa > pb:
        pa, pb = pb, pa
    return amount * Q96 / (pb - pa)


def nearest_tick(tick, fee):
    min_tick, max_tick = default_tick_range(fee)
    assert (
        min_tick <= tick <= max_tick
    ), f"Provided tick is out of bounds: {(min_tick, max_tick)}"
    tick_spacing = _tick_spacing[fee]
    rounded_tick_spacing = round(tick / tick_spacing) * tick_spacing
    if rounded_tick_spacing < min_tick:
        return rounded_tick_spacing + tick_spacing
    elif rounded_tick_spacing > max_tick:
        return rounded_tick_spacing - tick_spacing
    else:
        return rounded_tick_spacing
