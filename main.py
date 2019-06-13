from multiprocessing import Process
from data_process import result_process
from model_votes import vote_result
import sys
import model
from data_trans import pre_process
if __name__ == '__main__':
        pre_process()
        gpu_nums = len(sys.argv) - 1 #输入的gpu数量
        ensemble_per_part = 45//gpu_nums #每块GPU跑的次数
        processes = list()
        for i in range(gpu_nums):
            if i == 0: #第一个
                print('1'*10)
                last_ensemble_num = 0
                ensemble_num = ensemble_per_part
                p = Process(target=model.train, args=(sys.argv[i + 1],ensemble_num,last_ensemble_num))
                p.start()
                processes.append(p)
            elif i == gpu_nums-1: #最后一个部分,补全没有执行到45次的
                print('2'*10)
                last_ensemble_num = ensemble_per_part
                ensemble_num = 45 - (gpu_nums-1)*ensemble_per_part
                p = Process(target=model.train, args=(sys.argv[i + 1],ensemble_num,last_ensemble_num))
                p.start()
                processes.append(p)
            else:
                last_ensemble_num = ensemble_per_part
                ensemble_num = ensemble_per_part
                p = Process(target=model.train, args=(sys.argv[i + 1],ensemble_num,last_ensemble_num))
                p.start()
                processes.append(p)
        for p in processes:
            p.join()
        result_voted_result = vote_result('outputs/result_voted_result.json')
        result_process(result_voted_result,'outputs/final_data.json')