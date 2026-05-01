import { Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { GoldGrowthDynamics } from '../entities/gold-growth-dynamics.entity';
import { AnalyticsGoldGrowthDynamics } from '../entities/analytics-gold-growth-dynamics.entity';
import { AnalyticsGoldFiscalMonetary } from '../entities/analytics-gold-fiscal-monetary.entity';
import { AnalyticsGoldSocialWelfare } from '../entities/analytics-gold-social-welfare.entity';
import { AnalyticsClusters } from '../entities/analytics-clusters.entity';
import { AnalyticsGoldStructuralComposition } from '../entities/analytics-gold-structural-composition.entity';
import { AnalyticsGoldCrisisRisk } from '../entities/analytics-gold-crisis-risk.entity';

@Injectable()
export class CountriesService {
  constructor(
    @InjectRepository(GoldGrowthDynamics)
    private growthRepo: Repository<GoldGrowthDynamics>,
    @InjectRepository(AnalyticsGoldGrowthDynamics)
    private anGrowthRepo: Repository<AnalyticsGoldGrowthDynamics>,
    @InjectRepository(AnalyticsClusters)
    private clustersRepo: Repository<AnalyticsClusters>,
  ) { }
  async getCountryAnomalies(countryCode: string, threshold: number = 0.75) {
    const analyticsPayload = await this.getFullCountryAnalytics(countryCode);
    const anomalies: any[] = [];

    analyticsPayload.data.forEach(row => {
      const events: Array<{ type: string; score: number; actual: number }> = [];

      if (row.anomaly_growth >= threshold) {
        events.push({ type: 'Sốc Tăng trưởng', score: row.anomaly_growth, actual: row.actual_growth });
      }
      if (row.anomaly_debt >= threshold) {
        events.push({ type: 'Cảnh báo Nợ công', score: row.anomaly_debt, actual: row.actual_debt });
      }
      if (row.anomaly_reer_deviation >= threshold) {
        events.push({ type: 'Rủi ro Tiền tệ', score: row.anomaly_reer_deviation, actual: row.actual_reer_deviation });
      }

      if (events.length > 0) {
        anomalies.push({
          year: row.year,
          events: events
        });
      }
    });

    return anomalies;
  }

  async triggerAnalyticsWorker() {
    try {
      const response = await fetch('http://localhost:8001/analytics/run-all', {
        method: 'POST',
      });
      const data = await response.json();
      return data;
    } catch (error) {
      throw new Error(`Không thể kết nối đến Analytics Worker: ${error.message}`);
    }
  }
  async findAll() {
    const results = await this.growthRepo
      .createQueryBuilder('g')
      .select([
        'g.country_code as country_code',
        'g.country as country_name',
        'g.income_group as region',
      ])
      .distinct(true)
      .orderBy('g.country', 'ASC')
      .getRawMany();
    return results;
  }
  async getFullCountryAnalytics(countryCode: string) {
    const qb = this.growthRepo.createQueryBuilder('g');
    const rows = await qb
      .select([
        'g.country_code as country_code', 'g.year as year',
        'g.rGDP_growth_YoY as actual_growth', 'an_growth.rGDP_growth_YoY_trend as trend_growth', 'an_growth.rGDP_growth_YoY_anomaly_score as anomaly_growth',
        'an_fiscal.govdebt_GDP_actual as actual_debt', 'an_fiscal.govdebt_GDP_anomaly_score as anomaly_debt', 'an_fiscal.inflation_cpi_actual as actual_inflation',
        'an_social.poverty_headcount_actual as actual_poverty', 'an_social.unemployment_total_actual as actual_unemployment',
        'an_struct.manuf_va_share_actual as actual_manuf_share', 'an_struct.agri_va_share_actual as actual_agri_share',
        'an_risk.REER_deviation_actual as actual_reer_deviation', 'an_risk.REER_deviation_anomaly_score as anomaly_reer_deviation',
        'c.cluster_id as cluster_id',
        'g.completeness_score as completeness_score', 'an_struct.flag_score as flag_score'
      ])
      .leftJoin(AnalyticsGoldGrowthDynamics, 'an_growth', 'g.country_code = an_growth.country_code AND g.year = an_growth.year')
      .leftJoin(AnalyticsGoldFiscalMonetary, 'an_fiscal', 'g.country_code = an_fiscal.country_code AND g.year = an_fiscal.year')
      .leftJoin(AnalyticsGoldSocialWelfare, 'an_social', 'g.country_code = an_social.country_code AND g.year = an_social.year')
      .leftJoin(AnalyticsGoldStructuralComposition, 'an_struct', 'g.country_code = an_struct.country_code AND g.year = an_struct.year')
      .leftJoin(AnalyticsGoldCrisisRisk, 'an_risk', 'g.country_code = an_risk.country_code AND g.year = an_risk.year')
      .leftJoin(AnalyticsClusters, 'c', 'g.country_code = c.country_code AND g.year = c.year')
      .where('g.country_code = :countryCode', { countryCode })
      .orderBy('g.year', 'ASC')
      .getRawMany();

    const completeness = rows.length > 0
      ? rows.reduce((sum, r) => sum + (Number(r.completeness_score) || 0), 0) / rows.length
      : 0;
    const latestFlag = rows.length > 0 ? rows[rows.length - 1].flag_score : 0;

    return {
      meta: {
        country_code: countryCode,
        data_completeness: Math.round(completeness),
        flag_score: Number(latestFlag) || 0,
        latest_year: rows.length > 0 ? rows[rows.length - 1].year : null
      },
      data: rows
    };
  }
  async getClusterBenchmark(countryCode: string, indicator: string, year?: number | null) {
    const currentCluster = await this.clustersRepo.findOne({
      where: { country_code: countryCode, year: year ?? undefined },
      order: { year: 'DESC' }
    });
    if (!currentCluster) throw new Error('Không tìm thấy cụm cho quốc gia này');

    const members = await this.clustersRepo.find({ where: { cluster_id: currentCluster.cluster_id, year: currentCluster.year } });
    const memberCodes = members.map(m => m.country_code);

    const qb = this.growthRepo.createQueryBuilder('g')
      .select(['g.country_code as country_code', 'g.country as country_name', 'g.year as year'])
      .where('g.country_code IN (:...codes)', { codes: memberCodes })
      .where('g.year = :year', { year: currentCluster.year });

    if (indicator === 'rGDP_growth_YoY' || indicator === 'actual_growth') {
      qb.addSelect('g.rGDP_growth_YoY as value');
    } else if (indicator === 'govdebt_GDP' || indicator === 'actual_debt') {
      qb.addSelect('an_f.govdebt_GDP_actual as value').leftJoin(AnalyticsGoldFiscalMonetary, 'an_f', 'g.country_code = an_f.country_code AND g.year = an_f.year');
    } else if (indicator === 'actual_reer_deviation' || indicator === 'REER_deviation') {
      qb.addSelect('an_r.REER_deviation_actual as value').leftJoin(AnalyticsGoldCrisisRisk, 'an_r', 'g.country_code = an_r.country_code AND g.year = an_r.year');
    }

    const raw = await qb.getRawMany();
    const avg = raw.length > 0 ? raw.reduce((s, r) => s + (Number(r.value) || 0), 0) / raw.length : 0;
    return { cluster_id: currentCluster.cluster_id, indicator, year: currentCluster.year, average: avg, members: raw };
  }
}