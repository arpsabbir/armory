#!/usr/bin/python

from included.ModuleTemplate import ToolTemplate
from database.repositories import BaseDomainRepository, DomainRepository
import os
import json
import pdb

class Module(ToolTemplate):

    name = "aquatone-discover"
    binary_name = "aquatone-discover"

    def __init__(self, db):
        self.db = db
        self.Domain = DomainRepository(db, self.name)
        self.BaseDomain = BaseDomainRepository(db, self.name)


    def set_options(self):
        super(Module, self).set_options()

        self.options.add_argument('-d','--domain', help="Target domain for aquatone")
        self.options.add_argument('-f', '--file', help="Import domains from file")
        self.options.add_argument('-i', '--import_database', help="Import domains from database", action="store_true")
        self.options.add_argument('-r', '--rescan', help="Run aquatone on hosts that have already been processed.", action="store_true")
        self.options.set_defaults(timeout=None)

    
    def get_targets(self, args):
        '''
        This module is used to build out a target list and output file list, depending on the arguments. Should return a
        list in the format [(target, output), (target, output), etc, etc]
        '''
        targets = []

        if args.domain:
            created, domain = self.BaseDomain.find_or_create(domain=args.domain)
            targets.append(domain.domain)

        elif args.file:
            domainsFile = open(args.file).read().split('\n')
            for d in domainsFile:
                if d:
                    created, domain = self.BaseDomain.find_or_create(domain=args.domain)
                    targets.append(domain.domain)

        elif args.import_database:
            if args.rescan:
                all_domains = self.BaseDomain.all(scope_type="passive")
            else:
                all_domains = self.BaseDomain.all(tool=self.name, scope_type="passive")
            for d in all_domains:
                targets.append(d.domain)
            
        else:
            print("You need to supply domain(s).")

        output_path = os.path.join(self.base_config['PROJECT']['base_path'], 'aquatone' )

        
        
        if not os.path.exists(output_path):
            os.makedirs(output_path)

        res = []
        for t in targets:
            res.append({'target':t, 'output': "{}/{}/hosts.json".format(output_path, t) })

        return res

    def build_cmd(self, args):
        '''
        Create the actual command that will be executed. Use {target} and {output} as placeholders.
        ''' 
        cmd = self.binary + " -d {target} "
        
        if args.tool_args:
            cmd += args.tool_args

        return cmd

    def pre_run(self, args):
        output_path = self.base_config['PROJECT']['base_path']

        self.orig_home = os.environ['HOME']

        os.environ['HOME'] = output_path

    def process_output(self, cmds):
        '''
        Process the output generated by the earlier commands.
        '''
        for cmd in cmds:
            

            data2= json.loads(open(cmd['output']).read())

            for sub, ip in data2.iteritems():
                created = False
                new_domain = sub.lower()

                if new_domain:
                    created, subdomain = self.Domain.find_or_create(domain=new_domain)
            
        
        self.Domain.commit()

    def post_run(self, args):

        os.environ['HOME'] = self.orig_home