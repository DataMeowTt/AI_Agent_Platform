import { Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { GoldGrowthDynamics } from '../entities/gold-growth-dynamics.entity';
import { AnalyticsGoldGrowthDynamics } from '../entities/analytics-gold-growth-dynamics.entity';

@Injectable()
export class CountriesService {
  constructor(
    @InjectRepository(GoldGrowthDynamics)
    private growthRepo: Repository<GoldGrowthDynamics>,
    
    @InjectRepository(AnalyticsGoldGrowthDynamics)
    private analyticsGrowthRepo: Repository<AnalyticsGoldGrowthDynamics>,
  ) {}

  async findAll() {
    const results = await this.growthRepo
      .createQueryBuilder('g')
      .select([
        'g.country_code as country_code',
        'g.country as country_name',
      ])
      .distinct(true)
      .orderBy('g.country', 'ASC')
      .getRawMany();
    return results;
  }

  async getCountryAnalytics(countryCode: string) {
    return this.growthRepo
      .createQueryBuilder('g')
      .select([
        'g.country_code as country_code',
        'g.year as year',
        'g.rGDP_growth_YoY as actual',
        'a.rGDP_growth_YoY_trend as trend',
        'a.rGDP_growth_YoY_anomaly_score as anomaly_score'
      ])
      .innerJoin(
        AnalyticsGoldGrowthDynamics,
        'a',
        'g.country_code = a.country_code AND g.year = a.year'
      )
      .where('g.country_code = :countryCode', { countryCode })
      .orderBy('g.year', 'ASC')
      .getRawMany();
  }
}