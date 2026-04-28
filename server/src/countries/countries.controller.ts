import { Controller, Get, Param } from '@nestjs/common';
import { CountriesService } from './countries.service';

@Controller('api/v1/countries')
export class CountriesController {
  constructor(private readonly countriesService: CountriesService) {}

  @Get()
  async getCountries() {
    return this.countriesService.findAll();
  }

  @Get(':code/analytics')
  async getCountryAnalytics(@Param('code') code: string) {
    return this.countriesService.getCountryAnalytics(code.toUpperCase());
  }
}