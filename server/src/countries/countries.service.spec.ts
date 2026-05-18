import { Test, TestingModule } from '@nestjs/testing';
import { CountriesService } from './countries.service';
import { ConfigService } from '@nestjs/config';
import { BigQueryService } from '../bigquery/bigquery.service';
import { getRepositoryToken } from '@nestjs/typeorm';
import { GoldGrowthDynamics } from '../entities/gold-growth-dynamics.entity';
import { AnalyticsGoldGrowthDynamics } from '../entities/analytics-gold-growth-dynamics.entity';
import { AnalyticsClusters } from '../entities/analytics-clusters.entity';

describe('CountriesService', () => {
  let service: CountriesService;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [
        CountriesService,
        {
          provide: ConfigService,
          useValue: { get: jest.fn() },
        },
        {
          provide: BigQueryService,
          useValue: {},
        },
        {
          provide: getRepositoryToken(GoldGrowthDynamics),
          useValue: {},
        },
        {
          provide: getRepositoryToken(AnalyticsGoldGrowthDynamics),
          useValue: {},
        },
        {
          provide: getRepositoryToken(AnalyticsClusters),
          useValue: {},
        },
      ],
    }).compile();

    service = module.get<CountriesService>(CountriesService);
  });

  it('should be defined', () => {
    expect(service).toBeDefined();
  });
});
