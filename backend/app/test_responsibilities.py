#!/usr/bin/env python3

import sys
import os
sys.path.append('backend/app')

from models.models import Job
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Create engine
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://charbel:charbel@localhost:5437/matching_db')
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Get a job and check its responsibilities
session = SessionLocal()
try:
    job = session.query(Job).first()
    if job:
        print(f'Job ID: {job.id}')
        print(f'Job Title: {job.title}')
        print(f'Responsibilities type: {type(job.responsibilities)}')
        print(f'Responsibilities value: {job.responsibilities}')
        print(f'Responsibilities length: {len(job.responsibilities) if job.responsibilities else 0}')
        if job.responsibilities:
            for i, resp in enumerate(job.responsibilities):
                print(f'  {i}: "{resp}"')
    else:
        print('No jobs found in database')
finally:
    session.close() 