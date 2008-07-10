drop table votes;
drop table candidates;
drop table legalVoters;
drop table elections;

create table elections (
id serial,
shortname text not null,
name text not null,
info text not null,
url text not null,
start_date timestamp not null,
end_date timestamp not null,
max_seats integer not null,
-- NEW COL - Hold elections that allow multiple votes per user
votes_per_user integer not null,
-- NEW COL - Show results during a running election
public_results integer not null,
unique(shortname),
primary key (id)
);

create table legalVoters (
id serial,
election_id integer not null,
group_name text not null,
foreign key (election_id) references elections (id),
primary key (id)
);

create table candidates (
id serial,
election_id integer not null,
name text not null,
formalname text,
url text,
foreign key (election_id) references elections (id),
unique(id),
primary key (id, election_id)
);

create table votes (
id serial,
-- voter_id will refer to someones fas ID
voter text not null,
"timestamp" timestamp without time zone NOT NULL,
candidate_id integer not null,
weight integer not null,
election_id integer not null,
-- unique(voter_id, candidate_id, election_id),
foreign key (candidate_id) references candidates(id),
foreign key (election_id) references elections(id),
primary key (id)
);

create view votecount as select candidate_id, election_id, sum(weight) as novotes from votes group by candidate_id, election_id order by novotes desc;

create view fvotecount as select c.id, c.name, v.election_id, v.novotes from votecount v, candidates c where c.id = v.candidate_id order by novotesdesc;

create view uservotes as select election_id, voter, count(voter) as novotes from
votes group by election_id, voter;
