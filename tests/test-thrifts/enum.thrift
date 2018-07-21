enum Superhero {
    BATMAN,
    SUPERMAN = 2,
    SPIDERMAN = 0xa,
    WONDERWOMAN
}

service HeroService {
    Superhero getHero();
    void saveHero(0: Superhero hero);
}