import json

import pytest

from worker.messages import MAX_WORK_MS, InvalidMessage, Job, build_jobs, parse_job, process


def test_build_jobs_creates_sequential_ids():
    jobs = list(build_jobs(3, 250))
    assert jobs == [Job(1, 250), Job(2, 250), Job(3, 250)]


def test_build_jobs_supports_offset_and_empty_batches():
    assert list(build_jobs(0, 10)) == []
    assert [j.id for j in build_jobs(2, 10, start_id=100)] == [100, 101]


@pytest.mark.parametrize("count, work_ms", [(-1, 10), (1, -1), (1, MAX_WORK_MS + 1)])
def test_build_jobs_rejects_bad_arguments(count, work_ms):
    with pytest.raises(ValueError):
        list(build_jobs(count, work_ms))


def test_round_trip_through_bytes():
    job = Job(id=7, work_ms=1500)
    assert parse_job(job.to_bytes()) == job


@pytest.mark.parametrize(
    "body",
    [
        b"not json",
        b"{}",
        json.dumps({"id": 1}).encode(),
        json.dumps({"id": "abc", "work_ms": 10}).encode(),
        json.dumps({"id": 1, "work_ms": -5}).encode(),
        json.dumps({"id": 1, "work_ms": MAX_WORK_MS + 1}).encode(),
        json.dumps([1, 2]).encode(),
    ],
)
def test_parse_job_rejects_poison_messages(body):
    with pytest.raises(InvalidMessage):
        parse_job(body)


def test_process_simulates_work_for_the_requested_time():
    slept = []
    job = process(Job(id=3, work_ms=1200).to_bytes(), sleep=slept.append)
    assert job.id == 3
    assert slept == [1.2]


def test_process_does_no_work_for_poison_messages():
    slept = []
    with pytest.raises(InvalidMessage):
        process(b"garbage", sleep=slept.append)
    assert slept == []
