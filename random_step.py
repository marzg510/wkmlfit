from step_getter import StepGetter
import random

class RandomStepGetter(StepGetter):
    def __init__(self,from_int,to_int):
        self.from_int = from_int
        self.to_int = to_int
    def get_step(self,target_date):
        step = random.randint(self.from_int,self.to_int)
        return step

if __name__ == '__main__':
    stepper = RandomStepGetter(5000,10000)
    print(stepper.get_step(''))
