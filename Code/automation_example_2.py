# Create roads from a fixed amount of segments
import random
from trajectory_generator import  generate_trajectory

SEGMENT_COUNT = 5

MIN_LENGTH = 5
MAX_LENGTH = 50

MIN_RADIUS = 10
MAX_RADIUS = 50

MIN_ANGLE = 10
MAX_ANGLE = 90

def generate_random_road(n_segments):
    individual =  []
    for i in range(1, n_segments):
        individual.append(generate_random_road_segment())
    return individual


def generate_random_road_segment():
    if random.random() <= 0.3:
        return {'trajectory_segments':
                 [{'type': 'straight', 'length': random.randint(MIN_LENGTH, MAX_LENGTH)}]
                }
    elif random.random() <= 0.5:
        return {'trajectory_segments':
                    [ {'type': 'turn', 'angle': - random.randint(MIN_ANGLE, MAX_ANGLE),
                       'radius': random.randint(MIN_RADIUS, MAX_RADIUS)}]
                }
    else:
        return {'trajectory_segments':
                    [{'type': 'turn', 'angle': + random.randint(MIN_ANGLE, MAX_ANGLE),
                      'radius': random.randint(MIN_RADIUS, MAX_RADIUS)}]
                }



def replace_segment_mutation(road_segment):
    road_segment['trajectory_segments'] = generate_random_road_segment()['trajectory_segments']


def change_attribute_mutation(road_segment):
    if road_segment['trajectory_segments'][0]['type'] == 'straight':
        road_segment['trajectory_segments'][0]['length'] = random.randint(MIN_LENGTH, MAX_LENGTH)
    elif random.random() <= 0.5:
        sign = 1.0 if (random.random() <= 0.5) else -1.0
        road_segment['trajectory_segments'][0]['angle'] = random.randint(MIN_ANGLE, MAX_ANGLE) * sign
    else:
        road_segment['trajectory_segments'][0]['radius'] = random.randint(MIN_RADIUS, MAX_RADIUS)


def mutate(individual):

    # Clone the individual
    mutant = [dict(road_segment) for road_segment in individual]

    # Pick the road_segments to mutate
    for road_segment in individual:
        if random.random() <= 1 / len(individual):
            if random.random() <= 0.5:
                replace_segment_mutation(road_segment)
            else:
                change_attribute_mutation(road_segment)

    print("Mutated Road", mutant)



def main():
    population = [generate_random_road(5) for _ in range(1,6)]

    for individual in population:
        fitness = evalutate(individual)

    for _ in range(1, 10):
        mutant = mutate(individual)
        print(mutant)

    pass

if __name__ == '__main__':
    main()