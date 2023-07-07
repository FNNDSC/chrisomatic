# documentation: https://just.systems/man/en/

testing_harness := "./testing_harness"
minichris := "./testing_harness/miniChRIS-docker"

test: up
    cd {{testing_harness}} && docker compose run --rm --build dev

sim: up
    cd {{testing_harness}} && docker compose run --rm --build dev /t/simulation.sh

rebuild:
    cd {{testing_harness}} && docker compose build

clean:
    cd {{testing_harness}} && docker compose down -v --rmi local

up:
    cd {{minichris}} && docker compose up -d

down:
    cd {{minichris}} && docker compose down -v

nuke: down clean
