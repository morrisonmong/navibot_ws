"""This class stores all of the samples for training. It is able to
construct randomly selected batches of phi's from the stored history
"""

import numpy as np
import time
import tensorflow as tf

class DataSet(object): 
    def __init__(self, stateSize, maxSteps, phiLength, rng):
        '''Construct a DataSet
        Arguments:
        stateSize - number of parameters in state
        maxSteps - number of time steps to store
        phiLength - number of values to concatenate into a state
        rng - initialized np random number generator, used to
        choose random minibatches
        '''
        self.stateSize=stateSize
        self.maxSteps=maxSteps
        self.phiLength=phiLength
        self.rng=rng

        # Allocate circular buffers and indices
        self.states=np.zeros((self.maxSteps, self.stateSize),
                                dtype=np.float32)
        self.actions=np.zeros(self.maxSteps, dtype='int32')
        self.rewards=np.zeros(self.maxSteps, 
                                dtype=np.float32)
        self.nextStates=np.zeros((self.maxSteps, self.stateSize),
                                dtype=np.float32)
        self.terminal=np.zeros(self.maxSteps, dtype='bool')

        self.bottom=0
        self.top=0
        self.size=0

    def addSample(self, state, action, reward, nextState, terminal):
        """ Add a  time step record
        Arguments:
            state - observed state
            action - action chosen by the agent
            reward - reward received after taking the action
            terminal - boolean inidcating whether the episode ended 
            after this time step
        """
        self.states[self.top]=state
        self.actions[self.top]=action
        self.rewards[self.top]=reward
        self.nextStates[self.top]=nextState
        self.terminal[self.top]=terminal

        if self.size==self.maxSteps:
            self.bottom=(self.bottom+1)%self.maxSteps
        else:
            self.size+=1
        self.top=(self.top+1)%self.maxSteps
    
    def __len__(self):
        '''Return an approximate count for stored state transitions.'''
        return max(0, self.size - self.phiLength)

    def lastPhi(self):
        """Return the most recent phi (sequence of image frames)"""
        indexes=np.arange(self.top-self.phiLength, self.top)
        return self.states.take(indexes, axis=0, mode='wrap')

    def phi(self, state):
        """Return a phi (sequence of states), using the last phi length - 1,
        plus state.
        """
        indexes=np.arange(self.top-self.phiLength+1, self.top)
        phi=np.empty((self.phiLength, self.stateSize), 
                        dtype=np.float32)
        phi[0:self.phiLength-1]=self.states.take(indexes, axis=0, mode='wrap')
        phi[-1]=state
        return phi.reshape(1, self.stateSize*self.phiLength)

    def randomBatch(self, batchSize):
        """ Return cossreponding states, action, rewards, terminal status for
        batchSize. Randomly chosen state transitions
        """
        #Allocate space for the response
        states=np.zeros((batchSize,
                            self.phiLength,
                            self.stateSize),
                           dtype=np.float32)
        actions=np.zeros((batchSize,1),dtype='int32')
        rewards=np.zeros((batchSize,1),dtype=np.float32)
        nextStates=np.zeros((batchSize,
                            self.phiLength,
                            self.stateSize),
                           dtype=np.float32)
        terminal=np.zeros((batchSize,1),dtype='bool')

        count=0
        while count<batchSize:
            # Randomly choose a time step from the replay memory
            index=self.rng.randint(self.bottom,
                                   self.bottom+self.size-self.phiLength)
            # Both the before and after states contain phiLength
            # frames, overlapping except for the first and last
            allIndices=np.arange(index,index+self.phiLength)
            endIndex=index+self.phiLength-1
            
            # Check that the initial state corresponds entirely to a
            # single episode, meaning none but its last frame (the
            # second-to-last frame in imgs) may be terminal. If the last
            # frame of the initial state is terminal, then the last
            # frame of the transitioned state will actually be the first
            # frame of a new episode, which the Q learner recognizes and
            # handles correctly during training by zeroing the
            # discounted future reward estimate.
            #if np.any(self.terminal.take(allIndices[0:-2], mode='wrap')):
            #    continue

            # Add the state transition to the response.
            states[count] = self.states.take(allIndices, axis=0, mode='wrap')
            actions[count] = self.actions.take(endIndex, mode='wrap')
            rewards[count] = self.rewards.take(endIndex, mode='wrap')
            nextStates[count] = self.nextStates.take(allIndices, axis=0, mode='wrap')
            terminal[count] = self.terminal.take(endIndex, mode='wrap')
            count += 1

        return states.reshape(batchSize, self.stateSize*self.phiLength), actions.reshape(batchSize, ), rewards.reshape(batchSize, ), nextStates.reshape(batchSize, self.stateSize*self.phiLength), terminal.reshape(batchSize, )


# TESTING CODE BELOW THIS POINT...

def simple_tests():
    print('...Starting Simple Test')
    np.random.seed(222)
    dataset = DataSet(stateSize=3,
                      maxSteps=6, phiLength=4,
                      rng=np.random.RandomState(42))
    for i in range(10):
        state = np.random.random(3)*480
        action = np.random.randint(3)
        reward = np.random.random()
        terminal = False
        if np.random.random() < .05:
            terminal = True
        print('state', state)
        dataset.addSample(state, action, reward, terminal)
        print("S", dataset.states)
        print("A", dataset.actions)
        print("R", dataset.rewards)
        print("T", dataset.terminal)
        print("SIZE", dataset.size)
        print()
    print("LAST PHI", dataset.lastPhi())
    print
    print('BATCH', dataset.randomBatch(2))


def speed_tests():
    print('...Starting Speed Test')
    dataset = DataSet(stateSize=3,
                      maxSteps=20000, phiLength=4,
                      rng=np.random.RandomState(42))
    state = np.random.random(3)*480
    action = np.random.randint(3)
    reward = np.random.random()
    start = time.time()
    for i in range(100000):
        terminal = False
        if np.random.random() < .05:
            terminal = True
        dataset.addSample(state, action, reward, terminal)
    print("samples per second: ", 100000 / (time.time() - start))

    start = time.time()
    for i in range(200):
        a = dataset.randomBatch(32)
    print("batches per second: ", 200 / (time.time() - start))

    print('Dataset.lastPhi(): ', dataset.lastPhi())


def trivial_tests():
    print('...Starting Trivial Tests')
    dataset = DataSet(stateSize=1,
                      maxSteps=3, phiLength=2,
                      rng=np.random.RandomState(42))

    state1 = np.array([1], dtype=np.float32)
    state2 = np.array([2], dtype=np.float32)
    state3 = np.array([3], dtype=np.float32)

    dataset.addSample(state1, 1, 1, False)
    dataset.addSample(state2, 2, 2, False)
    dataset.addSample(state3, 2, 2, True)
    print("last Phi: ", dataset.lastPhi())
    print("random Batch: ", dataset.randomBatch(1))


def max_size_tests():
    print('...Starting Max Size Tests')
    dataset1 = DataSet(stateSize=3,
                      maxSteps=10, phiLength=4,
                      rng=np.random.RandomState(42))
    dataset2 = DataSet(stateSize=3,
                      maxSteps=1000, phiLength=4,
                      rng=np.random.RandomState(42))
    for i in range(100):
        state = np.random.random(3)*480
        action = np.random.randint(4)
        reward = np.random.random()
        terminal = False
        if np.random.random() < .05:
            terminal = True
        dataset1.addSample(state, action, reward, terminal)
        dataset2.addSample(state, action, reward, terminal)
        np.testing.assert_array_almost_equal(dataset1.lastPhi(),
                                             dataset2.lastPhi())
        print("Max Size Test passed")


def test_memory_usage_ok():
    print('...Starting Test Memory Usage ok')
    import memory_profiler
    dataset = DataSet(stateSize=3,
                      maxSteps=100000, phiLength=4,
                      rng=np.random.RandomState(42))
    last = time.time()

    for i in range(1000000000):
        if (i % 100000) == 0:
            print('i: ', i)
        dataset.addSample(np.random.random(3)*480, 1, 1, False)
        if i > 200000:
            states, actions, rewards, terminals = \
                                        dataset.randomBatch(32)
        if (i % 10007) == 0:
            print('Time: ', time.time() - last)
            mem_usage = memory_profiler.memory_usage(-1)
            print('Len(dataset): ', len(dataset), 'Memory Usage: ', mem_usage)
        last = time.time()


def main():
    speed_tests()
    test_memory_usage_ok()
    max_size_tests()
    simple_tests()

if __name__ == "__main__":
    main()

