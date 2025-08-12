import numpy as np
import random
import concurrent.futures
from config import MAX_CPU
import multiprocessing as mp


def evaluate_individual(objective_func, ind):
    """用于并行评估的辅助函数"""
    return objective_func(ind)


def de(objective_func, bounds, pop_size=10, gens=20, F=0.5, CR=0.9, parallel=False):
    """
    差分进化算法
    :param objective_func: 目标函数
    :param bounds: 参数边界 [(min, max), ...]
    :param pop_size: 种群大小
    :param gens: 迭代次数
    :param F: 缩放因子
    :param CR: 交叉概率
    :param parallel: 是否并行
    :return: (最优解, 最优值)
    """
    dim = len(bounds)
    pop = np.zeros((pop_size, dim))
    fitness = np.zeros(pop_size)

    # 初始化种群
    for i in range(pop_size):
        for d in range(dim):
            pop[i, d] = random.uniform(bounds[d][0], bounds[d][1])
        fitness[i] = objective_func(pop[i])

    # 记录最佳个体
    best_idx = np.argmin(fitness)
    best_fitness = fitness[best_idx]
    best_individual = pop[best_idx].copy()

    print(f"🎯 初始最优值: {best_fitness:.6f}")

    # 进化循环
    for gen in range(gens):
        print(f"\n📘 Generation {gen + 1}/{gens}")

        trial_pop = []
        for i in range(pop_size):
            # 选择三个不同的个体
            idxs = [idx for idx in range(pop_size) if idx != i]
            a, b, c = pop[random.sample(idxs, 3)]

            # 变异操作
            mutant = a + F * (b - c)

            # 边界处理
            for d in range(dim):
                mutant[d] = max(bounds[d][0], min(bounds[d][1], mutant[d]))

            # 交叉操作
            trial = pop[i].copy()
            cross_points = np.random.rand(dim) < CR
            if not np.any(cross_points):
                cross_points[random.randint(0, dim - 1)] = True
            trial[cross_points] = mutant[cross_points]
            trial_pop.append(trial)

        # # 评估试验种群
        # if parallel:
        #     print(f"⚙️ 并行评估 ({MAX_CPU}进程)")
        #     try:
        #         with concurrent.futures.ProcessPoolExecutor(max_workers=MAX_CPU) as executor:
        #             trial_fitness = list(executor.map(objective_func, trial_pop))
        #     except Exception as e:
        #         print(f"⚠️ 并行评估出错: {str(e)}")
        #         trial_fitness = [objective_func(ind) for ind in trial_pop]
        # else:
        #     trial_fitness = [objective_func(ind) for ind in trial_pop]
        # 评估试验种群
        if parallel:
            print(f"⚙️ 并行评估 ({MAX_CPU}进程)")
            try:
                with mp.Pool(processes=MAX_CPU) as pool:
                    # 使用starmap传递参数
                    args_list = [(objective_func, ind) for ind in trial_pop]
                    trial_fitness = pool.starmap(evaluate_individual, args_list)
            except Exception as e:
                print(f"⚠️ 并行评估出错: {str(e)}")
                # 回退到串行评估
                trial_fitness = [objective_func(ind) for ind in trial_pop]
        else:
            trial_fitness = [objective_func(ind) for ind in trial_pop]

        # 选择操作
        improved_count = 0
        for i in range(pop_size):
            if trial_fitness[i] < fitness[i]:
                pop[i] = trial_pop[i]
                fitness[i] = trial_fitness[i]
                improved_count += 1

                # 更新全局最优
                if trial_fitness[i] < best_fitness:
                    best_fitness = trial_fitness[i]
                    best_individual = trial_pop[i].copy()

        # 输出当前代信息
        print(f"🔄 改进个体: {improved_count}/{pop_size}")
        print(f"🔥 当前最优值: {best_fitness:.6f}")
        print(f"🧬 最优个体: {best_individual}")

    return best_individual, best_fitness
