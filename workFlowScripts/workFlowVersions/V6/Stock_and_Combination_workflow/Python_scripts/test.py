class Randomthing():
    count = 1
    def __init__(self, name) -> None:
        self.name = name
        self.unqiue_count = self.count
        Randomthing.count += 1
        print(self.unqiue_count)

thing1 = Randomthing('manu')
thing2 = Randomthing('anna')
thing3 = Randomthing('ppo')