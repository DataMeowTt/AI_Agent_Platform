import { Controller, Get, Param, Post } from '@nestjs/common';
import { CountriesService } from './countries.service';

@Controller('api/v1/countries')
export class CountriesController {
  constructor(private readonly countriesService: CountriesService) {}

  @Get()
  async getCountries() {
    return this.countriesService.findAll();
  }

  @Post('admin/trigger-worker')
  async triggerWorker() {
    return this.countriesService.triggerAnalyticsWorker();
  }

  @Get(':code/full-analytics')
  async getFullAnalytics(@Param('code') code: string) {
    return this.countriesService.getFullCountryAnalytics(code.toUpperCase());
  }

  @Get(':code/anomalies')
  async getAnomalies(@Param('code') code: string) {
    return this.countriesService.getCountryAnomalies(code.toUpperCase(), 0.75);
  }
}