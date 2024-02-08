import networkx as nx

DG = nx.DiGraph()

# DG.add_edge(1,1)

uniswapv2 = 'UniswapV2'
uniswapv3 = 'UniswapV3'
sushi2 = 'SushiSwapV2'
sushi3 = 'SushiSwapV2'

pair_list = ['weth-usdc', 'weth-usdt', 'wbtc-usdt', 'wbtc-usdc']
action = ['buy', 'sell']
DG.add_edge(f'{uniswapv2}_{pair_list[0]}_{action[0]}', f'{uniswapv3}_{pair_list[0]}_{action[1]}')
DG.add_edge(f'{uniswapv2}_{pair_list[0]}_{action[0]}', f'{uniswapv3}_{pair_list[1]}_{action[1]}')
print(DG.edges)
print(sorted(nx.simple_cycles(DG, length_bound=3)))

