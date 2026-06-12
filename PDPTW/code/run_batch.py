import os
import time
import pandas as pd
from pdptw import PDPTW
from alns import ALNS


def run_all_instances():
    # 存放算例的文件夹名称
    instances_dir = "Instances"

    # 1. 自动读取 Instances 文件夹下的所有标准算例
    all_files = os.listdir(instances_dir)
    # 过滤规则：只保留 .txt 结尾，且名字类似 lc101.txt, lrc208.txt 的标准文件
    target_files = [f for f in all_files if f.endswith('.txt') and len(f) <= 10 and f.startswith(('l', 'r', 'c'))]
    target_files.sort()  # 按字母顺序排序，方便查看进度

    results = []
    total_run_time = 0

    print("=" * 50)
    print(f"🚀 准备就绪！共检测到 {len(target_files)} 个标准算例。")
    print("=" * 50)

    for idx, file_name in enumerate(target_files):
        file_path = os.path.join(instances_dir, file_name)
        print(f"[{idx + 1:02d}/{len(target_files)}] 正在求解: {file_name:<10s} ...", end=" ", flush=True)

        start_time = time.time()

        try:
            # 读取问题实例
            problem = PDPTW.readInstance(file_path)

            # 初始化 ALNS (同步 main.py 里的各项参数)
            nDestroyOps = 10
            nRepairOps = 3
            minSizeNBH = 1
            nIterations = 5000
            maxPercentageNHB = 5
            tau = 0.1
            coolingRate = 0.9995
            decayParameter = 0.15
            noise = 0.015

            alns = ALNS(problem, nDestroyOps, nRepairOps, nIterations, minSizeNBH,
                        maxPercentageNHB, tau, coolingRate, decayParameter, noise)

            # 运行算法
            alns.execute()

            end_time = time.time()
            run_time = end_time - start_time
            total_run_time += run_time

            # 从 bestSolution 中提取真实成绩
            best_sol = alns.bestSolution
            nv = len(best_sol.routes)
            # 计算纯粹的物理行驶距离，剔除高额固定罚金
            td = sum(r.computeDistance() for r in best_sol.routes)

            print(f"✅ 完成 | 车辆数: {nv:2d} 辆 | 距离: {td:8.2f} | 耗时: {run_time:6.2f} 秒")

            # 记录结果字典
            results.append({
                "Instance": file_name.replace('.txt', ''),
                "NV (车辆数)": nv,
                "TD (总距离)": round(td, 2),
                "CPU Time (s)": round(run_time, 2)
            })

        except Exception as e:
            print(f"❌ 运行失败: {e}")

    # 2. 将结果转换为 Pandas 表格
    df = pd.DataFrame(results)

    # 3. 计算并打印统计信息
    avg_time = total_run_time / len(target_files) if target_files else 0
    print("\n" + "=" * 50)
    print(f"🎉 全部 56 个算例测试完毕！")
    print(f"⏱️ 全局平均运行时间: {avg_time:.2f} 秒/算例")

    # 4. 保存为 CSV，方便直接导入 Excel 写论文
    output_filename = "ALNS_Benchmark_Results.csv"
    df.to_csv(output_filename, index=False, encoding='utf-8-sig')
    print(f"📁 详细结果已保存至同级目录: {output_filename}")
    print("=" * 50)


if __name__ == "__main__":
    run_all_instances()