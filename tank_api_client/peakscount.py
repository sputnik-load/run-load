#!/usr/bin/python
# -*- coding: utf-8 -*-


import re


class PeaksCount(object):

    def __init__(self, version, log_type, log_file_path, thresholds):
        self.version = version
        self.log_type = log_type
        self.log_file_path = log_file_path
        self.thresholds = thresholds
        self.timeouts = {}
        self.reports = {}
        self.error_message = ''

    def _calc_timeouts(self):
        try:
            make_gen = lambda filename: (line.split('\t')
                                         for line in open(filename)
                                         if line.count('endTimeMillis', 0,
                                            len('endTimeMillis')) == 0 )

            if not self.log_file_path:
                self.error_message = "Log file with timeouts is not provided."
                return False

            try:
                file_try = make_gen(self.log_file_path)
                file_try.next()
            except:
                self.error_message = "Log file %s is empty." \
                                     % self.log_file_path
                return False

            file_list = make_gen(self.log_file_path)


            if self.log_type == 'jmeter':
                latency_idx, query_idx = 1, 2
                latency_multiplier = 10**(-3)
                status_code_idx = 6
            elif self.log_type == 'phantom':
                latency_idx, query_idx = 5, 1
                latency_multiplier = 10**(-6)
                status_code_idx = -1

            queries_dict = {}
            for line in file_list:
                latency = float(line[latency_idx]) * latency_multiplier
                query_tag = line[query_idx].lower()
                query_tag = re.sub('#\d+', '', query_tag)
                if not queries_dict.has_key(query_tag):
                    queries_dict[query_tag] = []
                queries_dict[query_tag].append(latency)

            values = {}
            values['timeouts'] = {}
            values['queries'] = {}
            for key in queries_dict.keys():
                values['queries'][key] = len([x
                                              for x in queries_dict[key]])
                if key in self.thresholds:
                    t_val = float(self.thresholds[key])
                    values['timeouts'][key] = \
                        (t_val, len([x for x in queries_dict[key]
                                     if x >= t_val]))
            if not values['timeouts']:
                self.error_message = "At least one sampleLabel should "
                self.error_message += "be specified in 'salts_timeouts' "
                self.error_message += "section of ini-file."
                return False
            self.timeouts = values
            return True
        except Exception, exc:
            self.timeouts = {}
            self.reports['raw'] = ''
            self.reports['jira'] = ''
            self.error_message = "Exception on timeouts obtaining: %s" % exc
            return False

    def _generate_raw_report(self):
        qcount = sum(self.timeouts['queries'].values())
        tcount = sum([v[1] for v in self.timeouts['timeouts'].values()])
        tags = self.timeouts['timeouts'].keys()
        tags.sort()
        max_tag_len = max(len(t) for t in tags)
        report = ''
        dash_line = ''

        qtype_header = u"Тип запроса"
        timeouts_header = u"Количество таймаутов"
        percents_header = u"Процент от числа запросов данного типа"
        colwidth_1st = max(len(qtype_header), max_tag_len)
        colwidth_2nd = len(timeouts_header)
        colwidth_3rd = len(percents_header)
        report += u"Всего запросов: %d, " % qcount
        report += u"всего таймаутов: %d. " % tcount
        report += u"Процент таймаутов: %f%%\n" % \
                    (float(tcount) / float(qcount) * 100)
        row_text = "| %s | %s | %s |" % (qtype_header.center(colwidth_1st),
                                        timeouts_header.center(colwidth_2nd),
                                        percents_header.center(colwidth_3rd))
        dash_line = "-" * len(row_text)
        report += dash_line + "\n"
        report += row_text + "\n"
        report += dash_line + "\n"

        for tag in tags:
            qcount = self.timeouts['queries'][tag]
            tcount = self.timeouts['timeouts'][tag][1]

            col_1st = tag.center(colwidth_1st)
            col_2nd = str(tcount).center(colwidth_2nd)
            col_3rd = str(float(tcount) / float(qcount) * 100).center(colwidth_3rd)
            report += "| %s | %s | %s |\n" % (col_1st, col_2nd, col_3rd)
            report += dash_line + '\n'

        self.reports['raw'] = report


    def _generate_jira_report(self):
        qcount = sum(self.timeouts['queries'].values())
        tcount = sum([v[1] for v in self.timeouts['timeouts'].values()])
        share = float(tcount) / float(qcount) * 100
        tags = self.timeouts['timeouts'].keys()
        tags.sort()
        max_tag_len = max(len(t) for t in tags)
        report = ''
        dash_line = ''


        report += u"||Версия||Всего запросов||Всего таймаутов||"
        report += u"Процент от общего числа запросов||\n"
        report += "|%s|%d|%d|%f%%|\n" % \
                    (self.version, qcount, tcount, share)
        report += u"||Тип запроса||Таймаут||Количество запросов||"
        report += u"Количество таймаутов||"
        report += u"Процент от числа запросов данного типа||\n"

        for tag in tags:
            qcount = self.timeouts['queries'][tag]
            tcount = self.timeouts['timeouts'][tag][1]
            report += "|%s|%s|%d|" % (tag,
                                      self.timeouts['timeouts'][tag][0],
                                      qcount)
            report += "%d|%f%%|\n" % (tcount,
                                      float(tcount) / float(qcount) * 100)

        self.reports['jira'] = report

    def get_report(self, report_type):
        if not self.timeouts:
            if not self._calc_timeouts():
                return self.error_message
        if not self.reports.get(report_type):
            if report_type == 'raw':
                self._generate_raw_report()
            elif report_type == 'jira':
                self._generate_jira_report()
            else:
                self.error_message = "Report Type is not supported."
        if self.error_message:
            return self.error_message
        return self.reports.get(report_type)
